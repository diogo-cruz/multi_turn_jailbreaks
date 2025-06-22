#!/usr/bin/env python3
"""
Analyze the full 300+ dataset to understand the breakdown.
"""

import pandas as pd

def analyze_dataset():
    """Analyze the full human evaluation dataset."""
    
    # Load human evaluations
    df = pd.read_csv('false_positive_annotations.csv')
    
    print("=== FULL DATASET ANALYSIS ===")
    print(f"Total records: {len(df)}")
    
    # Exclude fake_online_profile as instructed
    df_filtered = df[df['test_case'] != 'fake_online_profile']
    print(f"After excluding fake_online_profile: {len(df_filtered)}")
    
    print("\nDecision breakdown:")
    decision_counts = df_filtered['decision'].value_counts()
    print(decision_counts)
    for decision, count in decision_counts.items():
        print(f"  {decision}: {count} ({count/len(df_filtered)*100:.1f}%)")
    
    print("\nTest case breakdown:")
    test_case_counts = df_filtered['test_case'].value_counts()
    print(f"Number of unique test cases: {len(test_case_counts)}")
    print("Top 10 test cases:")
    for tc, count in test_case_counts.head(10).items():
        print(f"  {tc}: {count}")
    
    print("\nTactic breakdown:")
    tactic_counts = df_filtered['jailbreak_tactic'].value_counts()
    for tactic, count in tactic_counts.items():
        print(f"  {tactic}: {count}")
    
    # Check how many files exist in batch3A
    import os
    batch3a_dir = 'clean_results/final_runs/batch3A'
    available_files = []
    
    for _, row in df_filtered.iterrows():
        filename = row['filename']
        file_path = None
        
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                potential_path = os.path.join(tactic_path, filename)
                if os.path.exists(potential_path):
                    available_files.append(filename)
                    break
    
    print(f"\nFiles available in batch3A: {len(available_files)}/{len(df_filtered)}")
    print(f"Availability rate: {len(available_files)/len(df_filtered)*100:.1f}%")
    
    return df_filtered, available_files

if __name__ == "__main__":
    df, available = analyze_dataset()