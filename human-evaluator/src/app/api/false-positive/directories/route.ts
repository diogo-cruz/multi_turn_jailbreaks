import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const dirPath = searchParams.get('path');

    if (!dirPath) {
      return NextResponse.json({ error: 'Directory path is required' }, { status: 400 });
    }

    // Security check - ensure path is within the project directory
    const resolvedPath = path.resolve(dirPath);
    console.log(`Trying to scan directory: ${resolvedPath}`);
    
    if (!fs.existsSync(resolvedPath)) {
      console.log(`Directory does not exist: ${resolvedPath}`);
      return NextResponse.json({ error: 'Directory does not exist' }, { status: 404 });
    }
    
    console.log(`Directory exists, starting scan...`);

    // Calculate relative path from clean_results/final_runs/
    const baseResultsPath = '/Users/jaeha/repos/multi_turn_jailbreaks/clean_results/final_runs/';

    // Recursive function to find all .jsonl files
    function findJsonlFiles(dir: string): Array<{filename: string, fullPath: string, relativePath: string}> {
      const result: Array<{filename: string, fullPath: string, relativePath: string}> = [];
      
      try {
        const items = fs.readdirSync(dir);
        
        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);
          
          if (stat.isDirectory()) {
            // Recursively search subdirectories
            result.push(...findJsonlFiles(fullPath));
          } else if (item.endsWith('.jsonl')) {
            // Calculate relative path from the base directory
            const relativePath = path.relative(baseResultsPath, path.dirname(fullPath));
            result.push({
              filename: item,
              fullPath,
              relativePath
            });
          }
        }
      } catch (error) {
        console.error(`Error reading directory ${dir}:`, error);
      }
      
      return result;
    }

    const allJsonlFiles = findJsonlFiles(resolvedPath);
    console.log(`Found ${allJsonlFiles.length} .jsonl files in total`);
    
    const files = allJsonlFiles
      .map(({filename, fullPath, relativePath}) => {
        try {
          const content = fs.readFileSync(fullPath, 'utf-8');
          const lines = content.trim().split('\n');
          
          // Check if file has goal_achieved field
          let hasGoalAchieved = false;
          let goalAchieved = false;
          let fpAnnotated = false;
          let fpEvaluator = undefined;
          let fpDecision = undefined;
          
          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              
              // Check for goal_achieved (usually last line)
              if (data.goal_achieved !== undefined) {
                hasGoalAchieved = true;
                goalAchieved = data.goal_achieved;
              }
              
              // Check for existing false positive annotation
              if (data.fp_decision !== undefined) {
                fpAnnotated = true;
                fpEvaluator = data.fp_evaluator;
                fpDecision = data.fp_decision;
              }
            } catch (e) {
              // Skip invalid JSON lines
            }
          }

          return {
            filename,
            fullPath,
            relativePath,
            hasGoalAchieved,
            goalAchieved,
            fpAnnotated,
            fpEvaluator,
            fpDecision,
            isCorrupted: !hasGoalAchieved
          };

        } catch (error) {
          return {
            filename,
            fullPath,
            relativePath,
            hasGoalAchieved: false,
            goalAchieved: false,
            fpAnnotated: false,
            isCorrupted: true
          };
        }
      })
      .filter(file => !file.isCorrupted) // Skip corrupted files
      .filter(file => file.goalAchieved); // Only goal_achieved: true

    console.log(`After filtering: ${files.length} successful jailbreaks found`);
    const totalSuccessfulFiles = files.length;
    const annotatedFiles = files.filter(f => f.fpAnnotated).length;
    const pendingFiles = totalSuccessfulFiles - annotatedFiles;

    return NextResponse.json({
      path: resolvedPath,
      relativePath: path.relative(baseResultsPath, resolvedPath),
      totalSuccessfulFiles,
      annotatedFiles,
      pendingFiles,
      files: files.map(f => ({
        filename: f.filename,
        fullPath: f.fullPath,
        relativePath: f.relativePath,
        fpAnnotated: f.fpAnnotated,
        fpEvaluator: f.fpEvaluator,
        fpDecision: f.fpDecision
      }))
    });

  } catch (error) {
    console.error('Error scanning directory for successful jailbreaks:', error);
    return NextResponse.json({ error: 'Failed to scan directory' }, { status: 500 });
  }
}