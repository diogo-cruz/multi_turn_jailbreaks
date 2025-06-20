#!/usr/bin/env python3
"""
Fix CSV FP Mapping by Direct File Search
Since all files have FP data embedded, search for matching files directly.
"""

import json
import pandas as pd
from pathlib import Path
import re

def normalize_model_name(model_name):
    """Remove vendor prefix and normalize model name for matching."""
    if '/' in model_name:
        model_name = model_name.split('/')[-1]
    return model_name.replace('.', '-')

def find_matching_file(tactic, test_case, model, turn_type, base_dir):
    """Find the matching JSONL file for given parameters."""
    model_normalized = normalize_model_name(model)
    
    # Build search pattern
    pattern = f"{tactic}_{test_case}_{model_normalized}_{turn_type}_sample*.jsonl"
    
    # Search in the appropriate tactic subdirectory
    tactic_dir = base_dir / tactic
    if not tactic_dir.exists():
        return None
    
    # Try exact pattern match first
    matches = list(tactic_dir.glob(pattern))
    if matches:
        return matches[0]
    
    # If no exact match, try broader search
    for file_path in tactic_dir.glob("*.jsonl"):
        file_name = file_path.name
        if (tactic in file_name and 
            test_case in file_name and 
            turn_type in file_name and
            any(model_part in file_name for model_part in model_normalized.split('-'))):
            return file_path
    
    return None

def extract_fp_data_from_file(file_path):
    """Extract FP annotation from JSONL file."""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if 'fp_decision' in data:
                        return {
                            'fp_decision': data.get('fp_decision'),
                            'fp_evaluator': data.get('fp_evaluator'),
                            'fp_note': data.get('fp_note'),
                            'fp_timestamp': data.get('fp_timestamp')
                        }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def main():
    # Load the CSV
    df = pd.read_csv('csv_results/batch3A_results.csv')
    print(f"Loaded {len(df)} experiments")
    
    # Add FP columns
    df['fp_decision'] = None
    df['fp_evaluator'] = None  
    df['fp_note'] = None
    df['fp_timestamp'] = None
    
    base_dir = Path('clean_results/final_runs/batch3A')
    
    matched_count = 0
    fp_added_count = 0
    
    for idx, row in df.iterrows():
        if not row['goal_achieved']:
            continue  # Only process successful attacks
            
        tactic = row['jailbreak_tactic']
        test_case = row['test_case']
        model = row['target_model']
        turn_type = row['turn_type']
        
        # Find matching file
        file_path = find_matching_file(tactic, test_case, model, turn_type, base_dir)
        
        if file_path:
            matched_count += 1
            
            # Extract FP data
            fp_data = extract_fp_data_from_file(file_path)
            if fp_data:
                df.at[idx, 'fp_decision'] = fp_data['fp_decision']
                df.at[idx, 'fp_evaluator'] = fp_data['fp_evaluator']
                df.at[idx, 'fp_note'] = fp_data['fp_note'] 
                df.at[idx, 'fp_timestamp'] = fp_data['fp_timestamp']
                fp_added_count += 1
        else:
            print(f"No match found for: {tactic}, {test_case}, {normalize_model_name(model)}, {turn_type}")
    
    # Save result
    output_file = 'csv_results/batch3A_fixed_fp.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\nResults:")
    print(f"Matched {matched_count} successful attacks to files")
    print(f"Added FP data to {fp_added_count} rows")
    
    successful = df[df['goal_achieved'] == True]
    fp_data = df.dropna(subset=['fp_decision'])
    print(f"Total successful attacks: {len(successful)}")
    print(f"With FP data: {len(fp_data)}")
    print(f"Coverage: {len(fp_data)/len(successful)*100:.1f}%")
    
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()