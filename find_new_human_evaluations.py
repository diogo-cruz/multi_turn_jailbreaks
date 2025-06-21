#!/usr/bin/env python3
"""
Find new human evaluation cases that haven't been run through the updated AI meta-evaluator.
"""

import json
import pandas as pd
import os

def load_human_evaluations():
    """Load all human evaluations from the JSONL file."""
    human_evaluations = []
    with open('clean_results/false_positive_annotations.jsonl', 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            human_evaluations.append({
                'filename': data['filename'],
                'decision': data['decision'],
                'test_case': data.get('test_case', ''),
                'jailbreak_tactic': data.get('jailbreak_tactic', ''),
                'target_model': data.get('target_model', ''),
                'evaluator': data.get('evaluator', ''),
                'note': data.get('note', '')
            })
    return pd.DataFrame(human_evaluations)

def load_existing_ai_evaluations():
    """Load files that already have updated AI evaluations."""
    evaluated_files = set()
    
    # Files from our 77-case analysis
    df_77 = pd.read_csv('complete_77_cases_comparison.csv')
    evaluated_files.update(df_77['filename'].tolist())
    
    print(f"Previously evaluated files: {len(evaluated_files)}")
    return evaluated_files

def find_new_cases():
    """Find human evaluation cases that need AI meta-evaluation."""
    
    # Load human evaluations
    human_df = load_human_evaluations()
    print(f"Total human evaluations: {len(human_df)}")
    
    # Load existing AI evaluations
    existing_ai_files = load_existing_ai_evaluations()
    
    # Find new cases
    new_cases = human_df[~human_df['filename'].isin(existing_ai_files)]
    print(f"New cases needing AI evaluation: {len(new_cases)}")
    
    # Show breakdown by evaluator
    print("\\nBreakdown by human evaluator:")
    evaluator_counts = human_df['evaluator'].value_counts()
    for evaluator, count in evaluator_counts.items():
        new_count = len(new_cases[new_cases['evaluator'] == evaluator])
        print(f"  {evaluator}: {count} total, {new_count} new")
    
    # Show breakdown by decision
    print("\\nBreakdown by decision:")
    decision_counts = new_cases['decision'].value_counts()
    for decision, count in decision_counts.items():
        print(f"  {decision}: {count}")
    
    # Show breakdown by test case (top 10)
    print("\\nTop 10 test cases in new evaluations:")
    test_case_counts = new_cases['test_case'].value_counts().head(10)
    for test_case, count in test_case_counts.items():
        print(f"  {test_case}: {count}")
    
    # Show breakdown by tactic
    print("\\nBreakdown by jailbreak tactic:")
    tactic_counts = new_cases['jailbreak_tactic'].value_counts()
    for tactic, count in tactic_counts.items():
        print(f"  {tactic}: {count}")
    
    # Save new cases for processing
    new_cases.to_csv('new_human_evaluations_to_process.csv', index=False)
    print(f"\\nNew cases saved to: new_human_evaluations_to_process.csv")
    
    return new_cases

def check_file_availability(new_cases):
    """Check which of the new cases can be found in batch3A directory."""
    batch3a_dir = "clean_results/final_runs/batch3A"
    found_files = []
    missing_files = []
    
    for _, row in new_cases.iterrows():
        filename = row['filename']
        found = False
        
        # Search in all subdirectories of batch3A
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                file_path = os.path.join(tactic_path, filename)
                if os.path.exists(file_path):
                    found_files.append(file_path)
                    found = True
                    break
        
        if not found:
            missing_files.append(filename)
    
    print(f"\\nFile availability check:")
    print(f"  Found in batch3A: {len(found_files)}")
    print(f"  Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\\nFirst 10 missing files:")
        for i, filename in enumerate(missing_files[:10]):
            print(f"  {i+1}. {filename}")
        
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more")
    
    return found_files, missing_files

if __name__ == "__main__":
    print("Finding new human evaluation cases for AI meta-evaluation...")
    new_cases = find_new_cases()
    
    if len(new_cases) > 0:
        found_files, missing_files = check_file_availability(new_cases)
        print(f"\\nReady to process: {len(found_files)} files")
    else:
        print("\\nNo new cases to process!")