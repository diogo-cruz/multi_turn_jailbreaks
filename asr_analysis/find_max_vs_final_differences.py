#!/usr/bin/env python3
"""
Find examples where max score differs from final score for direct_request tactic.
Show the specific cases and point to their source JSONL files.
"""

import pandas as pd
import ast
import os

def safe_eval_scores(scores_str):
    """Safely evaluate scores string to list."""
    try:
        if pd.isna(scores_str):
            return []
        return ast.literal_eval(scores_str)
    except:
        return []

def main():
    # Load the master CSV
    df = pd.read_csv('/home/dcruz/multi_turn_jailbreaks/csv_results/master_results_verified.csv')
    print(f"Loaded {len(df)} total experiments")
    
    # Filter for direct_request tactic only
    df_direct = df[df['jailbreak_tactic'] == 'direct_request'].copy()
    print(f"After filtering for direct_request: {len(df_direct)} experiments")
    
    # Parse scores and calculate max vs final scores
    df_direct['scores_list'] = df_direct['scores'].apply(safe_eval_scores)
    df_direct['final_score'] = df_direct['scores_list'].apply(lambda x: x[-1] if x else 0.0)
    df_direct['max_score'] = df_direct['scores_list'].apply(lambda x: max(x) if x else 0.0)
    df_direct['score_difference'] = df_direct['max_score'] - df_direct['final_score']
    
    # Find cases where max score differs from final score
    different_cases = df_direct[df_direct['score_difference'] > 0.01].copy()
    print(f"Found {len(different_cases)} cases where max score > final score")
    
    if len(different_cases) == 0:
        print("No significant differences found!")
        return
    
    # Sort by score difference (largest differences first)
    different_cases = different_cases.sort_values('score_difference', ascending=False)
    
    print(f"\n{'='*80}")
    print(f"TOP EXAMPLES WHERE MAX SCORE > FINAL SCORE")
    print(f"{'='*80}")
    
    # Show top 10 examples
    for i, (_, row) in enumerate(different_cases.head(10).iterrows()):
        print(f"\nExample {i+1}:")
        print(f"  Test Case: {row['test_case']}")
        print(f"  Target Model: {row['target_model']}")
        print(f"  Turn Type: {row['turn_type']}")
        print(f"  Batch: {row['batch']}")
        print(f"  Scores: {row['scores_list']}")
        print(f"  Max Score: {row['max_score']:.3f}")
        print(f"  Final Score: {row['final_score']:.3f}")
        print(f"  Difference: {row['score_difference']:.3f}")
        
        # Try to find the source JSONL file
        source_file = row.get('source_file', '')
        if pd.isna(source_file) or source_file == '':
            # Try to construct likely filename based on available info
            if not pd.isna(row['batch']) and row['batch'] != '':
                # Look for files in clean_results
                batch = row['batch']
                tactic = row['jailbreak_tactic']
                test_case = row['test_case']
                model = row['target_model']
                turn_type = row['turn_type']
                
                # Common patterns for filenames
                possible_patterns = [
                    f"*/{tactic}/{tactic}_{test_case}_{model}_{turn_type}_sample*.jsonl",
                    f"*/{tactic}_{test_case}_{model}_{turn_type}_sample*.jsonl",
                    f"*/*{test_case}*{model}*{turn_type}*.jsonl"
                ]
                
                print(f"  Source File: Not specified in CSV")
                print(f"  Likely in: clean_results/final_runs/{batch}/")
                print(f"  Search patterns:")
                for pattern in possible_patterns:
                    print(f"    - {pattern}")
            else:
                print(f"  Source File: Not available")
        else:
            print(f"  Source File: {source_file}")
        
        print(f"  Timestamp: {row['timestamp']}")
    
    # Show distribution by turn type
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION BY TURN TYPE")
    print(f"{'='*80}")
    turn_type_dist = different_cases['turn_type'].value_counts()
    for turn_type, count in turn_type_dist.items():
        percentage = (count / len(different_cases)) * 100
        print(f"{turn_type}: {count} cases ({percentage:.1f}%)")
    
    # Show distribution by model
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION BY MODEL")
    print(f"{'='*80}")
    model_dist = different_cases['target_model'].value_counts()
    for model, count in model_dist.items():
        percentage = (count / len(different_cases)) * 100
        print(f"{model}: {count} cases ({percentage:.1f}%)")
    
    # Show statistics
    print(f"\n{'='*80}")
    print(f"STATISTICS")
    print(f"{'='*80}")
    print(f"Average difference: {different_cases['score_difference'].mean():.3f}")
    print(f"Median difference: {different_cases['score_difference'].median():.3f}")
    print(f"Max difference: {different_cases['score_difference'].max():.3f}")
    print(f"Min difference: {different_cases['score_difference'].min():.3f}")
    
    # Show average scores list length
    different_cases['scores_length'] = different_cases['scores_list'].apply(len)
    print(f"Average conversation length: {different_cases['scores_length'].mean():.1f} turns")
    print(f"Median conversation length: {different_cases['scores_length'].median():.1f} turns")
    
    # Save the results
    output_file = '/home/dcruz/multi_turn_jailbreaks/asr_analysis/max_vs_final_differences.csv'
    different_cases[['jailbreak_tactic', 'test_case', 'target_model', 'turn_type', 'batch', 
                    'scores_list', 'max_score', 'final_score', 'score_difference', 'timestamp', 
                    'source_file']].to_csv(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()