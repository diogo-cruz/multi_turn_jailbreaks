import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { EvaluationFile, ConversationTurn, EvaluationConfig, EvaluationCriteria, GoalAchieved } from '@/types/evaluation';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const filePath = searchParams.get('path');
    const filename = searchParams.get('filename');

    if (!filePath || !filename) {
      return NextResponse.json({ error: 'File path and filename are required' }, { status: 400 });
    }

    const fullPath = path.join(filePath, filename);
    
    if (!fs.existsSync(fullPath)) {
      return NextResponse.json({ error: 'File does not exist' }, { status: 404 });
    }

    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.trim().split('\n');

    let config: EvaluationConfig | null = null;
    let criteria: EvaluationCriteria | null = null;
    let goalAchieved: GoalAchieved | null = null;
    const turns: ConversationTurn[] = [];

    for (const line of lines) {
      try {
        const data = JSON.parse(line);
        
        // First line is usually the config
        if (data.target_model && data.jailbreak_tactic && !config) {
          config = data;
        }
        // Check for criteria
        else if (data.criteria && !criteria) {
          criteria = data;
        }
        // Check for goal achievement
        else if (data.goal_achieved !== undefined) {
          goalAchieved = data;
        }
        // Conversation turns
        else if (data.round !== undefined && data.user && data.assistant) {
          turns.push(data);
        }
      } catch (e) {
        console.error('Error parsing line:', line, e);
      }
    }

    if (!config) {
      return NextResponse.json({ error: 'Invalid file format - missing configuration' }, { status: 400 });
    }

    // Check if already human evaluated
    const humanEvaluated = turns.some(turn => turn.human_score !== undefined);
    const humanEvaluator = turns.find(turn => turn.human_evaluator)?.human_evaluator;

    const evaluationFile: EvaluationFile = {
      config,
      criteria,
      turns: turns.sort((a, b) => a.round - b.round),
      goalAchieved,
      filename,
      humanEvaluated,
      humanEvaluator
    };

    return NextResponse.json(evaluationFile);

  } catch (error) {
    console.error('Error reading file:', error);
    return NextResponse.json({ error: 'Failed to read file' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filePath, filename, turns, humanEvaluator } = body;

    if (!filePath || !filename || !turns || !humanEvaluator) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const fullPath = path.join(filePath, filename);
    
    if (!fs.existsSync(fullPath)) {
      return NextResponse.json({ error: 'File does not exist' }, { status: 404 });
    }

    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.trim().split('\n');
    const updatedLines: string[] = [];

    const timestamp = new Date().toISOString().replace(/[:.]/g, '_').slice(0, -5);

    for (const line of lines) {
      try {
        const data = JSON.parse(line);
        
        // Update conversation turns with human scores
        if (data.round !== undefined && data.user && data.assistant) {
          const updatedTurn = turns.find((t: ConversationTurn) => t.round === data.round);
          if (updatedTurn && updatedTurn.human_score !== undefined) {
            data.human_score = updatedTurn.human_score;
            data.human_evaluator = humanEvaluator;
            data.human_eval_timestamp = timestamp;
          }
        }
        
        updatedLines.push(JSON.stringify(data));
      } catch (e) {
        // Keep invalid lines as-is
        updatedLines.push(line);
      }
    }

    // Write updated content back to file
    fs.writeFileSync(fullPath, updatedLines.join('\n') + '\n');

    return NextResponse.json({ success: true, message: 'File updated successfully' });

  } catch (error) {
    console.error('Error updating file:', error);
    return NextResponse.json({ error: 'Failed to update file' }, { status: 500 });
  }
}