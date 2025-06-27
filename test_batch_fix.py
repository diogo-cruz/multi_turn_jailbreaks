#!/usr/bin/env python3
"""
Test script to verify the batch separation fix.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import comb
import os
from pathlib import Path
from typing import Dict, List, Optional
import ast

# Import utility functions
from asr_analysis_utils import (
    get_max_score_by_round, get_max_score_by_round_with_refusals,
    get_final_score, get_all_scores_including_refusals, read_json_file,
    load_jsonl_metadata, extract_sample_id_from_filename, expected_max_formula,
    exponential_approach, formula, fit_formula, get_tactic_style_and_batch_color,
    get_data_range, plot_combined_analysis, plot_averaged_analysis
)

# Control variables
EXTEND_XAXIS_FOR_REFUSALS = True
BATCH_NAME = "both"
INCLUDE_COMMAND = False

def extract_batch_metadata(batch_paths, max_rounds=8):
    """Extract metadata from batch files with improved batch handling."""
    single_turn_data = []
    multi_turn_data = []
    
    tactics_to_include = ['direct_request']
    if INCLUDE_COMMAND:
        tactics_to_include.append('command')
    
    for batch_path in batch_paths:
        batch_name = Path(batch_path).name
        root_path = Path(batch_path)
        jsonl_files = list(root_path.rglob('*.jsonl'))
        
        print(f"Found {len(jsonl_files)} JSONL files in {batch_name}...")
        
        for file_path in jsonl_files:
            metadata = load_jsonl_metadata(str(file_path))
            if metadata:
                tactic = metadata.get('jailbreak_tactic')
                
                if tactic in tactics_to_include:
                    metadata['file_path'] = str(file_path)
                    metadata['batch'] = batch_name
                    
                    if 'sample_id' not in metadata or metadata['sample_id'] is None:
                        metadata['sample_id'] = extract_sample_id_from_filename(file_path.name)
                    
                    data = read_json_file(str(file_path))
                    
                    if metadata.get('turn_type') == 'single':
                        final_score = get_final_score(data)
                        metadata['final_score'] = final_score
                        single_turn_data.append(metadata.copy())
                        
                    elif metadata.get('turn_type') == 'multi':
                        round_scores = get_max_score_by_round(data, max_rounds)
                        metadata_original = metadata.copy()
                        metadata_original.update(round_scores)
                        multi_turn_data.append(metadata_original)
    
    return {
        'single_turn': pd.DataFrame(single_turn_data),
        'multi_turn': pd.DataFrame(multi_turn_data)
    }

def analyze_single_turn_by_samples(df, max_samples=None):
    """Analyze single-turn data with proper batch grouping."""
    group_cols = ['test_case', 'target_model', 'jailbreak_tactic']
    if 'batch' in df.columns:
        group_cols.append('batch')
    
    grouped = df.groupby(group_cols)
    results = []
    
    for group_key, group in grouped:
        scores = group['final_score'].tolist()
        n = len(scores)
        
        if n >= 3:
            result_row = {
                'test_case': group_key[0],
                'target_model': group_key[1],
                'jailbreak_tactic': group_key[2],
                'n_samples_available': n
            }
            
            if len(group_key) > 3:
                result_row['batch'] = group_key[3]
            
            upper_limit = n if max_samples is None else min(n, max_samples)
            
            for s in range(1, upper_limit + 1):
                expected_max = expected_max_formula(scores, s, n)
                result_row[f'expected_max_score_{s}_samples'] = expected_max
            
            results.append(result_row)
    
    return pd.DataFrame(results)

def analyze_multi_turn_by_rounds(df, max_rounds=None):
    """Analyze multi-turn data with proper batch grouping."""
    group_cols = ['test_case', 'target_model', 'jailbreak_tactic']
    if 'batch' in df.columns:
        group_cols.append('batch')
    
    grouped = df.groupby(group_cols)
    results = []
    
    for group_key, group in grouped:
        if len(group) > 0:
            result_row = {
                'test_case': group_key[0],
                'target_model': group_key[1],
                'jailbreak_tactic': group_key[2],
                'n_conversations': len(group)
            }
            
            if len(group_key) > 3:
                result_row['batch'] = group_key[3]
            
            max_rounds_available = 0
            for _, conversation in group.iterrows():
                for col in conversation.index:
                    if 'max_score_by_' in col and '_rounds' in col:
                        try:
                            round_num = int(col.replace('max_score_by_', '').replace('_rounds', ''))
                            if not pd.isna(conversation[col]):
                                max_rounds_available = max(max_rounds_available, round_num)
                        except:
                            continue
            
            upper_limit = max_rounds_available if max_rounds is None else min(max_rounds_available, max_rounds)
            
            for r in range(1, upper_limit + 1):
                max_scores_for_round_r = []
                
                for _, conversation in group.iterrows():
                    scores_up_to_r = []
                    for round_num in range(1, r + 1):
                        score_col = f'max_score_by_{round_num}_rounds'
                        if score_col in conversation and not pd.isna(conversation[score_col]):
                            scores_up_to_r.append(conversation[score_col])
                    
                    if scores_up_to_r:
                        max_score_up_to_r = max(scores_up_to_r)
                        max_scores_for_round_r.append(max_score_up_to_r)
                    else:
                        max_scores_for_round_r.append(0.0)
                
                if max_scores_for_round_r:
                    avg_max_score = sum(max_scores_for_round_r) / len(max_scores_for_round_r)
                    result_row[f'max_score_{r}_rounds'] = avg_max_score
                else:
                    result_row[f'max_score_{r}_rounds'] = 0.0
            
            results.append(result_row)
    
    return pd.DataFrame(results)

def main():
    # Load data
    batch_data_paths = ['clean_results/final_runs/batch6A', 'clean_results/final_runs/batch6B']
    print(f"Loading data from both batches: {batch_data_paths}")
    batch_data = extract_batch_metadata(batch_data_paths)
    
    single_turn_df = batch_data['single_turn']
    multi_turn_df = batch_data['multi_turn']
    
    print(f"Single-turn data shape: {single_turn_df.shape}")
    print(f"Multi-turn data shape: {multi_turn_df.shape}")
    
    # Check batch distribution
    if 'batch' in single_turn_df.columns:
        print(f"Single-turn batch distribution: {single_turn_df['batch'].value_counts().to_dict()}")
    if 'batch' in multi_turn_df.columns:
        print(f"Multi-turn batch distribution: {multi_turn_df['batch'].value_counts().to_dict()}")
    
    # Analyze data
    print("\nAnalyzing single-turn data...")
    max_samples_param = None if EXTEND_XAXIS_FOR_REFUSALS else 8
    single_turn_results = analyze_single_turn_by_samples(single_turn_df, max_samples=max_samples_param)
    
    print("Analyzing multi-turn data...")
    max_rounds_param = None if EXTEND_XAXIS_FOR_REFUSALS else 8
    multi_turn_results = analyze_multi_turn_by_rounds(multi_turn_df, max_rounds=max_rounds_param)
    
    print(f"Single-turn results shape: {single_turn_results.shape}")
    print(f"Multi-turn results shape: {multi_turn_results.shape}")
    
    # Check if batch column is preserved in results
    if 'batch' in single_turn_results.columns:
        print(f"Single-turn results batch distribution: {single_turn_results['batch'].value_counts().to_dict()}")
    else:
        print("ERROR: Batch column missing from single-turn results!")
        
    if 'batch' in multi_turn_results.columns:
        print(f"Multi-turn results batch distribution: {multi_turn_results['batch'].value_counts().to_dict()}")
    else:
        print("ERROR: Batch column missing from multi-turn results!")
    
    # Create test plot to see if both batches appear
    print("\nCreating test plot to verify batch separation...")
    plot_averaged_analysis(single_turn_results, multi_turn_results, 
                          "BATCH6A+6B", EXTEND_XAXIS_FOR_REFUSALS, INCLUDE_COMMAND, BATCH_NAME,
                          title_suffix=" - Test Plot",
                          save_path="test_batch_separation_fixed.pdf")
    
    return single_turn_results, multi_turn_results

if __name__ == "__main__":
    single_turn_results, multi_turn_results = main()
    
    # Create additional plots
    print("\n=== CREATING ADDITIONAL PLOTS ===")
    
    # Combined analysis plot
    plot_combined_analysis(single_turn_results, multi_turn_results, 
                          "BATCH6A+6B", EXTEND_XAXIS_FOR_REFUSALS, INCLUDE_COMMAND, BATCH_NAME,
                          save_path="batch6a_6b_asr_rounds_samples_combined_fixed.pdf")
    
    print("All plots created successfully!")