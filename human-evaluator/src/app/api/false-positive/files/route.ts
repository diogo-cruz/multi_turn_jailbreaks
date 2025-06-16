import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { SuccessfulJailbreak, FalsePositiveAnnotation } from '@/types/false-positive';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const filePath = searchParams.get('path');
    const filename = searchParams.get('filename');

    console.log(`Loading file: ${filename} from path: ${filePath}`);

    if (!filePath || !filename) {
      return NextResponse.json({ error: 'File path and filename are required' }, { status: 400 });
    }

    const fullPath = path.join(filePath, filename);
    console.log(`Full file path: ${fullPath}`);
    
    if (!fs.existsSync(fullPath)) {
      console.log(`ERROR: File does not exist: ${fullPath}`);
      return NextResponse.json({ error: 'File does not exist' }, { status: 404 });
    }
    
    console.log(`File exists, reading content...`);

    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.trim().split('\n');

    let config: any = null;
    let goalAchieved = false;
    const turns: any[] = [];
    let fpAnnotated = false;
    let fpEvaluator = undefined;
    let fpDecision = undefined;
    let fpNote = undefined;

    for (const line of lines) {
      try {
        const data = JSON.parse(line);
        
        // First line is usually the config
        if (data.target_model && data.jailbreak_tactic && !config) {
          config = data;
        }
        // Check for goal achievement
        else if (data.goal_achieved !== undefined) {
          goalAchieved = data.goal_achieved;
        }
        // Conversation turns (entries with score field)
        else if (data.score !== undefined) {
          turns.push(data);
          
          // Check for existing false positive annotation in any turn
          if (data.fp_decision !== undefined && !fpAnnotated) {
            fpAnnotated = true;
            fpEvaluator = data.fp_evaluator;
            fpDecision = data.fp_decision;
            fpNote = data.fp_note;
          }
        }
      } catch (e) {
        console.error('Error parsing line:', line, e);
      }
    }

    if (!config) {
      return NextResponse.json({ error: 'Invalid file format - missing configuration' }, { status: 400 });
    }

    if (!goalAchieved) {
      return NextResponse.json({ error: 'File does not represent a successful jailbreak' }, { status: 400 });
    }

    console.log(`Parsed ${turns.length} conversation turns, goalAchieved: ${goalAchieved}`);
    console.log(`All scores in file:`, turns.map(t => t.score));
    
    // Find the jailbroken response (score = 1.0, or any non-refused if no score = 1.0)
    // Since we now filter only for goal_achieved: true, we need to find the best round
    let jailbrokenRounds = turns.filter(turn => turn.score === 1.0);
    console.log(`Found ${jailbrokenRounds.length} rounds with score = 1.0`);
    
    // If no score = 1.0, look for any non-refused turn with a numeric score
    if (jailbrokenRounds.length === 0) {
      jailbrokenRounds = turns.filter(turn => typeof turn.score === 'number' && turn.score !== "refused");
      console.log(`No score = 1.0 found, using ${jailbrokenRounds.length} rounds with numeric scores`);
    }
    
    // If still no suitable rounds, use the last turn
    if (jailbrokenRounds.length === 0 && turns.length > 0) {
      jailbrokenRounds = [turns[turns.length - 1]];
      console.log(`Using last turn as fallback`);
    }
    
    if (jailbrokenRounds.length === 0) {
      console.log(`ERROR: No suitable conversation turns found`);
      return NextResponse.json({ error: 'No suitable conversation turns found' }, { status: 400 });
    }
    
    // Use the first suitable round
    const jailbrokenRound = jailbrokenRounds[0];

    // Calculate relative path from clean_results/final_runs/
    const baseResultsPath = '/Users/jaeha/repos/multi_turn_jailbreaks/clean_results/final_runs/';
    const relativePath = path.relative(baseResultsPath, filePath);

    const successfulJailbreak: SuccessfulJailbreak = {
      config: {
        target_model: config.target_model,
        test_case: config.test_case,
        jailbreak_tactic: config.jailbreak_tactic,
        task: config.task,
        category: config.category || 'Unknown',
        timestamp: config.timestamp,
        turn_type: config.turn_type
      },
      finalRound: {
        round: jailbrokenRound.round,
        user: jailbrokenRound.user,
        assistant: jailbrokenRound.assistant,
        score: jailbrokenRound.score
      },
      filename,
      relativePath,
      goalAchieved,
      fpAnnotated,
      fpEvaluator,
      fpDecision,
      fpNote
    };

    return NextResponse.json(successfulJailbreak);

  } catch (error) {
    console.error('Error reading successful jailbreak file:', error);
    return NextResponse.json({ error: 'Failed to read file' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filePath, filename, evaluator, decision, note, finalRound } = body;

    if (!filePath || !filename || !evaluator || !decision || note === undefined) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const fullPath = path.join(filePath, filename);
    
    if (!fs.existsSync(fullPath)) {
      return NextResponse.json({ error: 'File does not exist' }, { status: 404 });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '_').slice(0, -5);

    // 1. Update the original file with minimal marking
    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.trim().split('\n');
    const updatedLines: string[] = [];

    for (const line of lines) {
      try {
        const data = JSON.parse(line);
        
        // Add FP annotation to the final round that was jailbroken
        // Match entries with score = 1.0
        if (data.score === 1.0) {
          data.fp_decision = decision;
          data.fp_note = note;
          data.fp_evaluator = evaluator;
          data.fp_timestamp = timestamp;
        }
        
        updatedLines.push(JSON.stringify(data));
      } catch (e) {
        // Keep invalid lines as-is
        updatedLines.push(line);
      }
    }

    // Write updated content back to original file
    fs.writeFileSync(fullPath, updatedLines.join('\n') + '\n');

    // 2. Write to independent annotation log
    const baseResultsPath = '/Users/jaeha/repos/multi_turn_jailbreaks/clean_results/final_runs/';
    const relativePath = path.relative(baseResultsPath, filePath);
    const annotationLogPath = path.join(path.dirname(fullPath), '../../../false_positive_annotations.jsonl');

    // Parse the file to get required information for the log
    const firstLine = JSON.parse(lines[0]);
    const finalRoundData = JSON.parse(lines.find(line => {
      try {
        const data = JSON.parse(line);
        // Find entry with score = 1.0
        return data.score === 1.0;
      } catch {
        return false;
      }
    }) || '{}');

    const annotation: FalsePositiveAnnotation = {
      relative_path: relativePath,
      filename,
      test_case: firstLine.test_case,
      jailbreak_tactic: firstLine.jailbreak_tactic,
      target_model: firstLine.target_model,
      task: firstLine.task,
      final_round: finalRound,
      evaluator,
      decision,
      note,
      jailbroken_output: finalRoundData.assistant || '',
      timestamp
    };

    // Append to annotation log
    fs.appendFileSync(annotationLogPath, JSON.stringify(annotation) + '\n');

    return NextResponse.json({ 
      success: true, 
      message: 'Annotation saved successfully',
      annotationLogPath
    });

  } catch (error) {
    console.error('Error saving false positive annotation:', error);
    return NextResponse.json({ error: 'Failed to save annotation' }, { status: 500 });
  }
}