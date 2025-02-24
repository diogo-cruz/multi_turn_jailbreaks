# Analysis Process Documentation

This document describes the process to generate and analyze the jailbreak evaluation results.

## Step 1: Data Preprocessing

Run `preprocess_results.py` which performs two main tasks:
1. Downloads the raw results from Drive to the `results_direct` folder
2. Processes these files to create cleaned filenames in the `analyzed_results` folder

**Note**: Recent setup changes may affect backwards compatibility of generated filenames. Some scripts may still reference the old folder name `results` instead of `analyzed_results`.

## Step 2: Manual Analysis with Claude

Each JSONL file needs to be analyzed following the instructions in `jailbreak_evaluation_instructions.md`. While this could be automated through the API, the current process involves:

1. Running `find_unanalyzed.sh` to identify which JSONL files haven't been analyzed yet
2. Using Cursor to analyze 4 files at a time with Claude
3. For each file, Claude generates an analysis MD file with the same name plus "_analysis" suffix

The analysis prompt focuses on identifying common issues like:
- Scoring metric inconsistencies
- Model response quality problems
- Attacker model limitations
- Test case definition issues
- Technical implementation problems

You can track progress using `count_unanalyzed.md` to see how many combinations remain to be analyzed.

## Step 3: Results Analysis and Visualization

Run `analyze_results.py` which:
1. Parses all the MD analysis files
2. Generates `results_data.csv` containing the quantitative analysis
3. Creates visualization plots in this folder (`analysis_output`) to help understand the patterns and issues in the jailbreak attempts

The plots help visualize various aspects of the jailbreak evaluation results, including success rates, common issues, and patterns across different models and approaches. 