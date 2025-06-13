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
    if (!fs.existsSync(resolvedPath)) {
      return NextResponse.json({ error: 'Directory does not exist' }, { status: 404 });
    }

    const files = fs.readdirSync(resolvedPath)
      .filter(file => file.endsWith('.jsonl'))
      .map(filename => {
        const filePath = path.join(resolvedPath, filename);
        const content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.trim().split('\n');
        
        // Check if file has human evaluation
        let humanEvaluated = false;
        let humanEvaluator = undefined;
        
        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.human_score !== undefined || data.human_evaluator !== undefined) {
              humanEvaluated = true;
              humanEvaluator = data.human_evaluator;
              break;
            }
          } catch (e) {
            // Skip invalid JSON lines
          }
        }

        return {
          filename,
          humanEvaluated,
          humanEvaluator
        };
      });

    const totalFiles = files.length;
    const evaluatedFiles = files.filter(f => f.humanEvaluated).length;
    const pendingFiles = totalFiles - evaluatedFiles;

    return NextResponse.json({
      path: resolvedPath,
      totalFiles,
      evaluatedFiles,
      pendingFiles,
      files
    });

  } catch (error) {
    console.error('Error reading directory:', error);
    return NextResponse.json({ error: 'Failed to read directory' }, { status: 500 });
  }
}