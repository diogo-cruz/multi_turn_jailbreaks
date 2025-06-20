#!/usr/bin/env python3
"""
Complete Batch3A CSV Generator with FP Data
Creates a complete CSV for batch3A with all FP annotations properly mapped.
"""

import json
import pandas as pd
from pathlib import Path

def get_model_name_from_path(model_with_vendor):
    """Extract model name without vendor prefix for file matching."""
    if '/' in model_with_vendor:
        return model_with_vendor.split('/')[-1]
    return model_with_vendor

def read_fp_data_from_file(file_path):
    """Read FP annotation data from JSONL file."""
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
    # Load the existing batch3A CSV
    df = pd.read_csv('csv_results/batch3A_results.csv')
    print(f"Loaded {len(df)} experiments from batch3A CSV")
    
    # Initialize FP columns
    df['fp_decision'] = None
    df['fp_evaluator'] = None
    df['fp_note'] = None
    df['fp_timestamp'] = None
    
    # Create file mapping
    batch3a_dir = Path('clean_results/final_runs/batch3A')
    file_mapping = {}
    
    for file_path in batch3a_dir.rglob('*.jsonl'):
        # Parse filename to extract key info
        name_parts = file_path.stem.split('_')
        if len(name_parts) >= 5:
            tactic = name_parts[0]
            test_case = name_parts[1]
            model = name_parts[2]
            turn_type = name_parts[3]
            
            # Handle multi-part model names and test cases
            i = 4
            while i < len(name_parts) and name_parts[i] not in ['single', 'multi']:
                if name_parts[i-1] != test_case:  # Avoid duplicating test case part
                    test_case += '_' + name_parts[i]
                i += 1
            
            if i < len(name_parts):
                turn_type = name_parts[i]
                i += 1
                while i < len(name_parts) and name_parts[i] not in ['single', 'multi']:
                    model += '-' + name_parts[i]
                    i += 1
            
            key = (tactic, test_case, model, turn_type)
            file_mapping[key] = file_path
    
    print(f"Built file mapping with {len(file_mapping)} files")
    
    # Process each row and try to match with files
    matched_count = 0
    fp_added_count = 0
    
    for idx, row in df.iterrows():
        tactic = row['jailbreak_tactic']
        test_case = row['test_case'] 
        model_full = row['target_model']
        model = get_model_name_from_path(model_full)
        turn_type = row['turn_type']
        
        # Try exact match first
        key = (tactic, test_case, model, turn_type)
        matched_file = file_mapping.get(key)
        
        # If no exact match, try partial matching
        if not matched_file:
            for file_key, file_path in file_mapping.items():
                file_tactic, file_test, file_model, file_turn = file_key
                if (tactic == file_tactic and 
                    test_case == file_test and 
                    turn_type == file_turn and
                    (model in file_model or file_model in model)):
                    matched_file = file_path
                    break
        
        if matched_file:
            matched_count += 1
            
            # Only process if this was a successful attack
            if row['goal_achieved']:
                fp_data = read_fp_data_from_file(matched_file)
                if fp_data:
                    df.at[idx, 'fp_decision'] = fp_data['fp_decision']
                    df.at[idx, 'fp_evaluator'] = fp_data['fp_evaluator'] 
                    df.at[idx, 'fp_note'] = fp_data['fp_note']
                    df.at[idx, 'fp_timestamp'] = fp_data['fp_timestamp']
                    fp_added_count += 1
    
    print(f"Matched {matched_count}/{len(df)} rows to files")
    print(f"Added FP data to {fp_added_count} successful attacks")
    
    # Save the enhanced CSV
    output_file = 'csv_results/batch3A_complete_with_fp.csv'
    df.to_csv(output_file, index=False)
    print(f"Saved complete CSV to {output_file}")
    
    # Print summary stats
    successful = df[df['goal_achieved'] == True]
    fp_data = df.dropna(subset=['fp_decision'])
    print(f"\nSummary:")
    print(f"Total experiments: {len(df)}")
    print(f"Successful attacks: {len(successful)}")
    print(f"With FP data: {len(fp_data)}")
    print(f"Coverage: {len(fp_data)/len(successful)*100:.1f}%")

if __name__ == "__main__":
    main()