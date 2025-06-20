#!/usr/bin/env python3
"""
Final CSV Fix - Direct Annotation Mapping
Create exact mapping between CSV rows and annotated files.
"""

import json
import pandas as pd
from pathlib import Path

def load_annotations():
    """Load all annotations with full file paths."""
    annotations = {}
    with open('clean_results/false_positive_annotations.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                file_path = f'clean_results/final_runs/{ann["relative_path"]}/{ann["filename"]}'
                annotations[file_path] = ann
    return annotations

def extract_file_info(file_path):
    """Extract tactic, test_case, model, turn_type from file path."""
    path = Path(file_path)
    
    # Get tactic from parent directory
    tactic = path.parent.name
    
    # Parse filename: {tactic}_{test_case}_{model}_{turn_type}_sample1_{timestamp}.jsonl
    name_parts = path.stem.split('_')
    if len(name_parts) < 6:  # tactic, test_case_parts, model, turn_type, sample1, timestamp_parts
        return None, None, None, None
    
    # Remove tactic prefix - check if filename starts with tactic
    if '_'.join(name_parts[:len(tactic.split('_'))]) == tactic:
        name_parts = name_parts[len(tactic.split('_')):]
    
    # Find turn_type and sample1 positions
    turn_idx = -1
    sample_idx = -1
    
    for i, part in enumerate(name_parts):
        if part in ['single', 'multi']:
            turn_idx = i
        elif part == 'sample1':
            sample_idx = i
            break
    
    if turn_idx == -1 or sample_idx == -1 or sample_idx != turn_idx + 2:
        return None, None, None, None
    
    turn_type = name_parts[turn_idx]
    model = name_parts[turn_idx - 1]  # Part just before turn_type
    
    # Test case is everything from start to model (exclusive)
    test_case_parts = name_parts[:turn_idx - 1]
    test_case = '_'.join(test_case_parts)
    
    return tactic, test_case, model, turn_type

def normalize_model_for_comparison(model):
    """Normalize model name for comparison."""
    # Remove vendor prefix if present
    if '/' in model:
        model = model.split('/')[-1]
    return model

def main():
    # Load annotations
    print("Loading annotations...")
    annotations = load_annotations()
    print(f"Loaded {len(annotations)} annotations")
    
    # Create mapping from file info to annotation
    file_info_to_annotation = {}
    for file_path, ann in annotations.items():
        if 'batch3A' not in file_path:
            continue
            
        tactic, test_case, model, turn_type = extract_file_info(file_path)
        if all([tactic, test_case, model, turn_type]):
            key = (tactic, test_case, model, turn_type)
            file_info_to_annotation[key] = ann
    
    print(f"Created mapping for {len(file_info_to_annotation)} batch3A files")
    
    # Load CSV
    df = pd.read_csv('csv_results/batch3A_results.csv')
    print(f"Loaded {len(df)} CSV rows")
    
    # Add FP columns
    df['fp_decision'] = None
    df['fp_evaluator'] = None
    df['fp_note'] = None
    df['fp_timestamp'] = None
    
    matched_count = 0
    successful_count = 0
    
    for idx, row in df.iterrows():
        if not row['goal_achieved']:
            continue
            
        successful_count += 1
        
        csv_tactic = row['jailbreak_tactic']
        csv_test_case = row['test_case']
        csv_model = normalize_model_for_comparison(row['target_model'])
        csv_turn_type = row['turn_type']
        
        # Try exact match first
        key = (csv_tactic, csv_test_case, csv_model, csv_turn_type)
        if key in file_info_to_annotation:
            ann = file_info_to_annotation[key]
            df.at[idx, 'fp_decision'] = ann['decision']
            df.at[idx, 'fp_evaluator'] = ann['evaluator']
            df.at[idx, 'fp_note'] = ann['note']
            df.at[idx, 'fp_timestamp'] = ann['timestamp']
            matched_count += 1
            continue
        
        # Try fuzzy matching if no exact match
        found = False
        for (f_tactic, f_test_case, f_model, f_turn_type), ann in file_info_to_annotation.items():
            if (csv_tactic == f_tactic and 
                csv_test_case == f_test_case and
                csv_turn_type == f_turn_type and
                (csv_model in f_model or f_model in csv_model or
                 any(part in f_model for part in csv_model.split('-')))):
                
                df.at[idx, 'fp_decision'] = ann['decision']
                df.at[idx, 'fp_evaluator'] = ann['evaluator']
                df.at[idx, 'fp_note'] = ann['note']
                df.at[idx, 'fp_timestamp'] = ann['timestamp']
                matched_count += 1
                found = True
                break
        
        if not found:
            print(f"No match for: {csv_tactic}, {csv_test_case}, {csv_model}, {csv_turn_type}")
    
    # Save result
    output_file = 'csv_results/batch3A_complete_fp.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\nResults:")
    print(f"Total successful attacks: {successful_count}")
    print(f"Matched to annotations: {matched_count}")
    print(f"Coverage: {matched_count/successful_count*100:.1f}%")
    
    # Verify FP stats
    fp_data = df.dropna(subset=['fp_decision'])
    tp_count = len(fp_data[fp_data['fp_decision'] == 'true_positive'])
    fp_count = len(fp_data[fp_data['fp_decision'] == 'false_positive'])
    
    print(f"True positives: {tp_count}")
    print(f"False positives: {fp_count}")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()