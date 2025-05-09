#!/usr/bin/env python3
import pandas as pd
import os
import json
from collections import defaultdict

def main():
    """Simple script to check ASR calculation for one model."""
    # Path to the CSV file
    csv_path = os.path.join("public", "data", "master_results.csv")
    
    try:
        # Read the CSV file
        print(f"Loading CSV from {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded {len(df)} rows from CSV")
        
        # Get a list of all models in the dataset
        model_names = df['target_model'].unique()
        print(f"Found {len(model_names)} unique models:")
        for i, model in enumerate(model_names[:10]):
            print(f"  {i+1}. {model}")
        
        if len(model_names) > 0:
            # Select the first model for analysis
            selected_model = model_names[0]
            print(f"\nAnalyzing model: {selected_model}")
            
            # Filter data for this model
            model_df = df[df['target_model'] == selected_model]
            print(f"Found {len(model_df)} rows for this model")
            
            # Filter to zero temperature entries
            zero_temp_df = model_df[
                pd.isna(model_df['target_temp']) | 
                (model_df['target_temp'] == 0)
            ]
            print(f"After filtering to zero temperature: {len(zero_temp_df)} rows")
            
            # Calculate single-turn and multi-turn success rates
            single_turn_df = zero_temp_df[zero_temp_df['turn_type'] == 'single']
            multi_turn_df = zero_temp_df[zero_temp_df['turn_type'] == 'multi']
            
            print(f"Single-turn rows: {len(single_turn_df)}")
            print(f"Multi-turn rows: {len(multi_turn_df)}")
            
            # Group by test case and calculate success rates
            single_test_cases = {}
            multi_test_cases = {}
            
            # Process single-turn
            for test_case, group in single_turn_df.groupby('test_case'):
                # Group by tactic
                tactic_success_rates = []
                
                for tactic, tactic_group in group.groupby('jailbreak_tactic'):
                    success_count = sum(tactic_group['goal_achieved'] == True)
                    total_count = len(tactic_group)
                    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                    tactic_success_rates.append(success_rate)
                    print(f"  Single-turn test case: {test_case}, tactic: {tactic}, success rate: {success_rate:.2f}% ({success_count}/{total_count})")
                
                # Take the maximum success rate for this test case
                if tactic_success_rates:
                    max_rate = max(tactic_success_rates)
                    single_test_cases[test_case] = max_rate
                    print(f"  Max single-turn success rate for {test_case}: {max_rate:.2f}%")
            
            # Process multi-turn
            for test_case, group in multi_turn_df.groupby('test_case'):
                # Group by tactic
                tactic_success_rates = []
                
                for tactic, tactic_group in group.groupby('jailbreak_tactic'):
                    success_count = sum(tactic_group['goal_achieved'] == True)
                    total_count = len(tactic_group)
                    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
                    tactic_success_rates.append(success_rate)
                    print(f"  Multi-turn test case: {test_case}, tactic: {tactic}, success rate: {success_rate:.2f}% ({success_count}/{total_count})")
                
                # Take the maximum success rate for this test case
                if tactic_success_rates:
                    max_rate = max(tactic_success_rates)
                    multi_test_cases[test_case] = max_rate
                    print(f"  Max multi-turn success rate for {test_case}: {max_rate:.2f}%")
            
            # Calculate ASR by averaging the maximum success rates
            single_turn_asr = sum(single_test_cases.values()) / len(single_test_cases) if single_test_cases else 0
            multi_turn_asr = sum(multi_test_cases.values()) / len(multi_test_cases) if multi_test_cases else 0
            
            print(f"\nFINAL ASR RESULTS for {selected_model}:")
            print(f"  Single-turn ASR: {single_turn_asr:.2f}% ({len(single_test_cases)} test cases)")
            print(f"  Multi-turn ASR: {multi_turn_asr:.2f}% ({len(multi_test_cases)} test cases)")
            
        else:
            print("No models found in the dataset")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 