#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

def get_best_score(scores_str):
    """
    Get the best score from a list of scores.
    
    Args:
        scores_str: String representation of scores list
    
    Returns:
        float: Best score, or 0 if invalid
    """
    try:
        scores_list = eval(scores_str)
        if not scores_list:
            return 0
        # Validate that all scores are in 0-1 range
        for score in scores_list:
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                print(f"Warning: Invalid score {score} found in {scores_str}")
                return 0
        return max(scores_list)  # Using max since higher is better
    except:
        return 0

def analyze_model_asr_differences(csv_file='results_strongreject_transformed.csv'):
    """
    Analyze differences in Attack Success Rate (ASR) between models.
    
    Args:
        csv_file: CSV file containing the data
    """
    # Load the data
    csv_path = os.path.join('csv_results', csv_file)
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Get unique models
    models = sorted(df['target_model'].unique())
    model_short_names = [model.split('/')[-1] for model in models]
    
    # Create a dictionary to store results for each model, turn type, tactic, and test case
    all_results = {}
    
    # Process each model
    for model in models:
        model_df = df[df['target_model'] == model]
        model_short_name = model.split('/')[-1]
        
        all_results[model_short_name] = {}
        
        # Process each turn type
        for turn_type in ['multi', 'single']:
            turn_df = model_df[model_df['turn_type'] == turn_type]
            
            if turn_df.empty:
                continue
                
            all_results[model_short_name][turn_type] = {}
            
            # Process each test case and tactic combination
            for test_case in turn_df['test_case'].unique():
                for tactic in turn_df['jailbreak_tactic'].unique():
                    combo_df = turn_df[(turn_df['test_case'] == test_case) & 
                                    (turn_df['jailbreak_tactic'] == tactic)]
                    
                    if combo_df.empty:
                        continue
                    
                    # Calculate mean best score
                    scores = [get_best_score(s) for s in combo_df['scores']]
                    if scores:
                        mean_score = np.mean(scores)
                        all_results[model_short_name][turn_type][(test_case, tactic)] = mean_score
    
    # Calculate overall ASR for each model and turn type
    overall_asr = {}
    for model_name in all_results:
        overall_asr[model_name] = {}
        for turn_type in all_results[model_name]:
            scores = list(all_results[model_name][turn_type].values())
            if scores:
                overall_asr[model_name][turn_type] = np.mean(scores)
    
    # Sort models by overall multi-turn ASR for better visualization
    sorted_models = sorted(overall_asr.keys(), 
                           key=lambda x: overall_asr[x].get('multi', 0), 
                           reverse=True)
    
    # Print overall ASR results
    print("\n=== Overall Attack Success Rate (ASR) by Model ===")
    print(f"{'Model':<25} {'Multi-Turn ASR':>15} {'Single-Turn ASR':>20} {'Difference (M-S)':>20}")
    print("-" * 80)
    
    for model in sorted_models:
        multi_asr = overall_asr[model].get('multi', 0)
        single_asr = overall_asr[model].get('single', 0)
        diff = multi_asr - single_asr
        
        print(f"{model:<25} {multi_asr:>15.4f} {single_asr:>20.4f} {diff:>20.4f}")
    
    # Visualize overall ASR comparison
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(sorted_models))
    width = 0.35
    
    multi_values = [overall_asr[model].get('multi', 0) for model in sorted_models]
    single_values = [overall_asr[model].get('single', 0) for model in sorted_models]
    
    rects1 = plt.bar(x - width/2, multi_values, width, label='Multi-Turn')
    rects2 = plt.bar(x + width/2, single_values, width, label='Single-Turn')
    
    plt.xlabel('Model')
    plt.ylabel('Average ASR (Best Score)')
    plt.title('Attack Success Rate Comparison Between Models')
    plt.xticks(x, sorted_models, rotation=45, ha='right')
    plt.legend()
    plt.ylim(0, 1.0)
    
    plt.tight_layout()
    plt.savefig('model_asr_comparison.png', dpi=300)
    plt.close()
    
    # Calculate per-tactic ASR differences
    print("\n=== Attack Success Rate (ASR) by Tactic ===")
    
    tactic_diff = {}
    for model in all_results:
        if 'multi' not in all_results[model] or 'single' not in all_results[model]:
            continue
            
        for key, multi_score in all_results[model]['multi'].items():
            test_case, tactic = key
            
            if key in all_results[model]['single']:
                single_score = all_results[model]['single'][key]
                
                if tactic not in tactic_diff:
                    tactic_diff[tactic] = {}
                
                if model not in tactic_diff[tactic]:
                    tactic_diff[tactic][model] = []
                    
                tactic_diff[tactic][model].append(multi_score - single_score)
    
    # Calculate average tactic differences
    tactic_avg_diff = {}
    for tactic in tactic_diff:
        tactic_avg_diff[tactic] = {}
        for model in tactic_diff[tactic]:
            tactic_avg_diff[tactic][model] = np.mean(tactic_diff[tactic][model])
    
    # Print tactic differences
    print("\nAverage Multi-Turn vs Single-Turn ASR Difference by Tactic")
    print(f"{'Tactic':<25}", end="")
    
    for model in sorted_models:
        print(f" {model:>12}", end="")
    print()
    
    print("-" * (25 + 12 * len(sorted_models)))
    
    for tactic in sorted(tactic_avg_diff.keys()):
        print(f"{tactic:<25}", end="")
        
        for model in sorted_models:
            diff = tactic_avg_diff[tactic].get(model, float('nan'))
            if not np.isnan(diff):
                print(f" {diff:>+12.4f}", end="")
            else:
                print(f" {'N/A':>12}", end="")
        print()
    
    # Calculate per-test case ASR differences
    print("\n=== Attack Success Rate (ASR) by Test Case ===")
    
    testcase_diff = {}
    for model in all_results:
        if 'multi' not in all_results[model] or 'single' not in all_results[model]:
            continue
            
        for key, multi_score in all_results[model]['multi'].items():
            test_case, tactic = key
            
            if key in all_results[model]['single']:
                single_score = all_results[model]['single'][key]
                
                if test_case not in testcase_diff:
                    testcase_diff[test_case] = {}
                
                if model not in testcase_diff[test_case]:
                    testcase_diff[test_case][model] = []
                    
                testcase_diff[test_case][model].append(multi_score - single_score)
    
    # Calculate average test case differences
    testcase_avg_diff = {}
    for test_case in testcase_diff:
        testcase_avg_diff[test_case] = {}
        for model in testcase_diff[test_case]:
            testcase_avg_diff[test_case][model] = np.mean(testcase_diff[test_case][model])
    
    # Print top test cases with largest differences
    avg_by_testcase = {}
    for test_case in testcase_avg_diff:
        values = [v for v in testcase_avg_diff[test_case].values() if not np.isnan(v)]
        if values:
            avg_by_testcase[test_case] = np.mean(values)
    
    top_testcases = sorted(avg_by_testcase.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
    
    print("\nTop Test Cases with Largest Multi-Turn vs Single-Turn ASR Differences (Averaged Across Models)")
    print(f"{'Test Case':<35} {'Avg Difference':>15}")
    print("-" * 50)
    
    for test_case, diff in top_testcases:
        print(f"{test_case:<35} {diff:>+15.4f}")
    
    # Create a heatmap for multi-turn advantage by model and test category
    # First, categorize test cases
    test_categories = {
        'harm': ['how_to_make_meth', 'self_harm', 'human_trafficking', 'build_bomb', 'security_exploit'],
        'hate': ['hate_speech', 'sexist_joke'],
        'misinformation': ['misinformation', 'misinformation_annexation_of_crimea_russia'],
        'corporate': ['corporate_secrets', 'corporate_sabotage'],
        'misc': ['steganography', 'cryptocurrency', 'hacking_tips', 'bypass_ai_protection']
    }
    
    # Map each test case to its category
    test_to_category = {}
    for category, tests in test_categories.items():
        for test in tests:
            test_to_category[test] = category
    
    # For unmatched test cases, assign to 'other'
    for test in testcase_avg_diff:
        if test not in test_to_category:
            test_to_category[test] = 'other'
    
    # Prepare data for heatmap
    heatmap_data = []
    for model in sorted_models:
        for test_case in testcase_avg_diff:
            if model in testcase_avg_diff[test_case]:
                diff = testcase_avg_diff[test_case][model]
                category = test_to_category.get(test_case, 'other')
                heatmap_data.append({
                    'Model': model,
                    'Test Category': category,
                    'Difference': diff
                })
    
    if heatmap_data:
        heatmap_df = pd.DataFrame(heatmap_data)
        pivot_df = heatmap_df.pivot_table(
            values='Difference',
            index='Model',
            columns='Test Category',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_df, cmap='RdBu_r', center=0, annot=True, fmt='.3f', linewidths=.5)
        plt.title('Multi-Turn Advantage by Model and Test Category')
        plt.tight_layout()
        plt.savefig('model_testcategory_advantage_heatmap.png', dpi=300)
        plt.close()
    
    # Calculate mean advantage for each model on each tactic
    tactic_advantage_data = []
    for tactic in tactic_avg_diff:
        for model in sorted_models:
            if model in tactic_avg_diff[tactic]:
                diff = tactic_avg_diff[tactic][model]
                tactic_advantage_data.append({
                    'Model': model,
                    'Tactic': tactic,
                    'Advantage': diff
                })
    
    if tactic_advantage_data:
        tactic_df = pd.DataFrame(tactic_advantage_data)
        pivot_tactic = tactic_df.pivot_table(
            values='Advantage',
            index='Model',
            columns='Tactic',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(14, 8))
        sns.heatmap(pivot_tactic, cmap='RdBu_r', center=0, annot=True, fmt='.3f', linewidths=.5)
        plt.title('Multi-Turn Advantage by Model and Jailbreak Tactic')
        plt.tight_layout()
        plt.savefig('model_tactic_advantage_heatmap.png', dpi=300)
        plt.close()
        
    print("\nAnalysis complete. Visualizations saved as PNG files.")

if __name__ == "__main__":
    analyze_model_asr_differences() 