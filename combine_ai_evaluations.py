#!/usr/bin/env python3
"""
Combine the original 100 AI evaluations with the new human-overlap evaluations
"""

import pandas as pd
import os
from datetime import datetime

def combine_evaluations():
    """Combine the original and new AI evaluations."""
    
    # Load original 100 evaluations
    original_file = 'random_100_meta_evaluation_results/issue_scores_20250617_005322.csv'
    original_df = pd.read_csv(original_file)
    print(f"Original AI evaluations: {len(original_df)} files")
    
    # Load new human-overlap evaluations
    new_file = 'human_overlap_meta_evaluation_results/issue_scores_20250617_064158.csv'
    new_df = pd.read_csv(new_file)
    print(f"New human-overlap AI evaluations: {len(new_df)} files")
    
    # Check for any overlaps (there should be 5)
    overlap_files = set(original_df['file_name']) & set(new_df['file_name'])
    print(f"Overlapping files between datasets: {len(overlap_files)}")
    
    if overlap_files:
        print("Overlapping files:")
        for f in sorted(overlap_files):
            print(f"  - {f}")
        
        # Remove overlaps from new dataset (keep original)
        new_df = new_df[~new_df['file_name'].isin(overlap_files)]
        print(f"After removing overlaps, new dataset has: {len(new_df)} files")
    
    # Combine datasets
    combined_df = pd.concat([original_df, new_df], ignore_index=True)
    print(f"Combined dataset: {len(combined_df)} files")
    
    # Save combined dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "combined_meta_evaluation_results"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"issue_scores_combined_{timestamp}.csv")
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Combined evaluations saved to: {output_file}")
    
    # Show statistics
    print(f"\nCombined Dataset Statistics:")
    print(f"Total files: {len(combined_df)}")
    print(f"Tactics distribution:")
    print(combined_df['tactic'].value_counts())
    print(f"\nTarget models distribution:")
    print(combined_df['target_model'].value_counts().head(10))
    
    return output_file

if __name__ == "__main__":
    combined_file = combine_evaluations() 