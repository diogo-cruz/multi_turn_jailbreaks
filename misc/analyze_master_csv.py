#!/usr/bin/env python3
"""
Analyze Master CSV - Detailed Breakdown
Generate comprehensive statistics from the master CSV file.
"""

import pandas as pd
from collections import defaultdict

def main():
    # Load the master CSV
    df = pd.read_csv('csv_results/master_results_verified.csv')
    print(f"Loaded {len(df)} total experiments from master CSV")
    
    # Clean model names for better readability
    df['model_clean'] = df['target_model'].apply(lambda x: x.split('/')[-1] if '/' in str(x) else x)
    
    # 1. Results by batch and model
    print("\n" + "="*80)
    print("RESULTS BY BATCH AND MODEL")
    print("="*80)
    
    batch_model_stats = []
    for batch in sorted(df['batch'].unique()):
        if pd.isna(batch):
            continue
        batch_df = df[df['batch'] == batch]
        print(f"\n{batch.upper()}: {len(batch_df)} total experiments")
        print("-" * 60)
        
        model_counts = batch_df['model_clean'].value_counts().sort_index()
        for model, count in model_counts.items():
            print(f"  {model}: {count}")
            batch_model_stats.append({
                'batch': batch,
                'model': model,
                'count': count
            })
    
    # 2. Results by batch and test case + tactic combination
    print("\n" + "="*80)
    print("RESULTS BY BATCH AND TEST CASE + TACTIC COMBINATION")
    print("="*80)
    
    batch_combo_stats = []
    for batch in sorted(df['batch'].unique()):
        if pd.isna(batch):
            continue
        batch_df = df[df['batch'] == batch]
        print(f"\n{batch.upper()}: {len(batch_df)} total experiments")
        print("-" * 60)
        
        # Create combination column
        batch_df = batch_df.copy()
        batch_df['combo'] = batch_df['jailbreak_tactic'].astype(str) + ' + ' + batch_df['test_case'].astype(str)
        
        combo_counts = batch_df['combo'].value_counts().sort_index()
        for combo, count in combo_counts.items():
            if 'nan' not in combo:  # Skip invalid combinations
                print(f"  {combo}: {count}")
                tactic, test_case = combo.split(' + ')
                batch_combo_stats.append({
                    'batch': batch,
                    'tactic': tactic,
                    'test_case': test_case,
                    'combination': combo,
                    'count': count
                })
    
    # 3. Overall statistics
    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    
    print(f"\nTotal experiments across all batches: {len(df)}")
    print(f"Unique batches: {len(df['batch'].unique())}")
    print(f"Unique models: {len(df['model_clean'].unique())}")
    print(f"Unique test cases: {len(df['test_case'].unique())}")
    print(f"Unique tactics: {len(df['jailbreak_tactic'].unique())}")
    
    # Top models across all batches
    print(f"\nTop 10 models across all batches:")
    top_models = df['model_clean'].value_counts().head(10)
    for model, count in top_models.items():
        print(f"  {model}: {count}")
    
    # Top test cases across all batches
    print(f"\nTop 10 test cases across all batches:")
    top_test_cases = df['test_case'].value_counts().head(10)
    for test_case, count in top_test_cases.items():
        print(f"  {test_case}: {count}")
    
    # Top tactics across all batches
    print(f"\nTop 10 tactics across all batches:")
    top_tactics = df['jailbreak_tactic'].value_counts().head(10)
    for tactic, count in top_tactics.items():
        print(f"  {tactic}: {count}")
    
    # 4. Save detailed breakdowns to CSV files
    batch_model_df = pd.DataFrame(batch_model_stats)
    batch_combo_df = pd.DataFrame(batch_combo_stats)
    
    batch_model_df.to_csv('csv_results/batch_model_breakdown.csv', index=False)
    batch_combo_df.to_csv('csv_results/batch_combo_breakdown.csv', index=False)
    
    print(f"\nDetailed breakdowns saved to:")
    print(f"  - csv_results/batch_model_breakdown.csv")
    print(f"  - csv_results/batch_combo_breakdown.csv")

if __name__ == "__main__":
    main()