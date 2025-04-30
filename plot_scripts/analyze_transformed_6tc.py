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
        return max(scores_list)  # Higher values indicate more successful jailbreaks
    except:
        return 0

def analyze_transformed_6tc(csv_file='results_strongreject_transformed.csv'):
    """
    Analyze the 6 test cases in the transformed dataset where scores are in 0-1 range.
    
    Args:
        csv_file: CSV file containing the transformed data
    """
    # Load the data
    csv_path = os.path.join('csv_results', csv_file)
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Create output directory
    output_dir = 'transformed_6tc_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter to just the 6 test cases we're interested in
    six_tc = ['hate_speech', 'steal_info', 'deoderant_flamethrower', 'disarm_police', 'leak_photos', 'women_drivers']
    df_6tc = df[df['test_case'].isin(six_tc)]
    
    # Get unique models
    models = sorted(df_6tc['target_model'].unique())
    model_short_names = [model.split('/')[-1] for model in models]
    
    # Create a dictionary to store results for each model, turn type, tactic, and test case
    all_results = {}
    
    # Process each model
    for model in models:
        model_df = df_6tc[df_6tc['target_model'] == model]
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
    print("\n=== Overall Attack Success Rate (ASR) by Model (6TC Dataset - Transformed) ===")
    print(f"{'Model':<25} {'Multi-Turn ASR':>15} {'Single-Turn ASR':>20} {'Difference (M-S)':>20}")
    print("-" * 80)
    
    # Also save to file
    with open(os.path.join(output_dir, 'overall_asr_results.txt'), 'w') as f:
        f.write("=== Overall Attack Success Rate (ASR) by Model (6TC Dataset - Transformed) ===\n")
        f.write(f"{'Model':<25} {'Multi-Turn ASR':>15} {'Single-Turn ASR':>20} {'Difference (M-S)':>20}\n")
        f.write("-" * 80 + "\n")
    
        for model in sorted_models:
            multi_asr = overall_asr[model].get('multi', 0)
            single_asr = overall_asr[model].get('single', 0)
            diff = multi_asr - single_asr
            
            output_line = f"{model:<25} {multi_asr:>15.4f} {single_asr:>20.4f} {diff:>20.4f}"
            print(output_line)
            f.write(output_line + "\n")
    
    # Visualize overall ASR comparison
    plt.figure(figsize=(12, 7))
    
    x = np.arange(len(sorted_models))
    width = 0.35
    
    multi_values = [overall_asr[model].get('multi', 0) for model in sorted_models]
    single_values = [overall_asr[model].get('single', 0) for model in sorted_models]
    
    rects1 = plt.bar(x - width/2, multi_values, width, label='Multi-Turn', color='#ff7f0e', alpha=0.8)
    rects2 = plt.bar(x + width/2, single_values, width, label='Single-Turn', color='#1f77b4', alpha=0.8)
    
    # Add value labels on top of each bar
    for i, v in enumerate(multi_values):
        plt.text(i - width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
    
    for i, v in enumerate(single_values):
        plt.text(i + width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Average ASR (Best Score 0-1 Scale)', fontsize=12)
    plt.title('Attack Success Rate Comparison Between Models (6TC Dataset - Transformed)', fontsize=14)
    plt.xticks(x, sorted_models, rotation=45, ha='right', fontsize=10)
    plt.legend(loc='upper right', fontsize=10)
    plt.ylim(0, 1.1)
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'model_asr_comparison.png'), dpi=300)
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
    header_line = f"{'Tactic':<25}"
    for model in sorted_models:
        header_line += f" {model:>12}"
    print(header_line)
    
    separator = "-" * (25 + 12 * len(sorted_models))
    print(separator)
    
    # Also save to file
    with open(os.path.join(output_dir, 'tactic_asr_results.txt'), 'w') as f:
        f.write("Average Multi-Turn vs Single-Turn ASR Difference by Tactic\n")
        f.write(header_line + "\n")
        f.write(separator + "\n")
    
        for tactic in sorted(tactic_avg_diff.keys()):
            line = f"{tactic:<25}"
            
            for model in sorted_models:
                diff = tactic_avg_diff[tactic].get(model, float('nan'))
                if not np.isnan(diff):
                    line += f" {diff:>+12.4f}"
                else:
                    line += f" {'N/A':>12}"
            
            print(line)
            f.write(line + "\n")
    
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
    
    # Print all test cases with differences
    avg_by_testcase = {}
    for test_case in testcase_avg_diff:
        values = [v for v in testcase_avg_diff[test_case].values() if not np.isnan(v)]
        if values:
            avg_by_testcase[test_case] = np.mean(values)
    
    all_testcases = sorted(avg_by_testcase.items(), key=lambda x: abs(x[1]), reverse=True)
    
    print("\nTest Cases with Multi-Turn vs Single-Turn ASR Differences (Averaged Across Models)")
    print(f"{'Test Case':<35} {'Avg Difference':>15}")
    print("-" * 50)
    
    # Also save to file
    with open(os.path.join(output_dir, 'testcase_asr_results.txt'), 'w') as f:
        f.write("Test Cases with Multi-Turn vs Single-Turn ASR Differences (Averaged Across Models)\n")
        f.write(f"{'Test Case':<35} {'Avg Difference':>15}\n")
        f.write("-" * 50 + "\n")
    
        for test_case, diff in all_testcases:
            output_line = f"{test_case:<35} {diff:>+15.4f}"
            print(output_line)
            f.write(output_line + "\n")
    
    # Create a heatmap for multi-turn advantage by model and test case
    test_data = []
    for model in sorted_models:
        for test_case in six_tc:
            if test_case in testcase_avg_diff and model in testcase_avg_diff[test_case]:
                diff = testcase_avg_diff[test_case][model]
                test_data.append({
                    'Model': model,
                    'Test Case': test_case,
                    'Difference': diff
                })
    
    if test_data:
        test_df = pd.DataFrame(test_data)
        pivot_test = test_df.pivot_table(
            values='Difference',
            index='Model',
            columns='Test Case',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_test, cmap='RdBu_r', center=0, annot=True, fmt='.3f', linewidths=.5, 
                    vmin=-0.4, vmax=0.4)
        plt.title('Multi-Turn Advantage by Model and Test Case (6TC Dataset - Transformed)', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'model_testcase_advantage_heatmap.png'), dpi=300)
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
        sns.heatmap(pivot_tactic, cmap='RdBu_r', center=0, annot=True, fmt='.3f', linewidths=.5,
                   vmin=-0.4, vmax=0.4)
        plt.title('Multi-Turn Advantage by Model and Jailbreak Tactic (6TC Dataset - Transformed)', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'model_tactic_advantage_heatmap.png'), dpi=300)
        plt.close()
    
    # Create detailed per-model visualizations
    create_model_score_plots(df_6tc, output_dir)
        
    print(f"\nAnalysis complete. Results and visualizations saved to {output_dir} directory.")

def create_model_score_plots(df, output_dir):
    """
    Create model-specific visualizations showing scores by test case and tactic.
    
    Args:
        df: DataFrame with the data
        output_dir: Directory to save output files
    """
    # Create subdirectory for model plots
    model_dir = os.path.join(output_dir, 'model_plots')
    os.makedirs(model_dir, exist_ok=True)
    
    # Get unique models
    models = sorted(df['target_model'].unique())
    tactics = sorted(df['jailbreak_tactic'].unique())
    test_cases = sorted(df['test_case'].unique())
    
    # Create comparison plots for each model
    for model in models:
        model_short = model.split('/')[-1]
        model_df = df[df['target_model'] == model]
        
        # Create a score comparison bar chart
        plt.figure(figsize=(14, 10))
        
        # Get multi-turn and single-turn data
        multi_df = model_df[model_df['turn_type'] == 'multi']
        single_df = model_df[model_df['turn_type'] == 'single']
        
        # Calculate mean scores per test case
        multi_scores = {}
        single_scores = {}
        
        for tc in test_cases:
            multi_tc_scores = []
            for scores_str in multi_df[multi_df['test_case'] == tc]['scores']:
                try:
                    scores = eval(scores_str)
                    if scores:
                        multi_tc_scores.append(max(scores))
                except:
                    pass
            
            single_tc_scores = []
            for scores_str in single_df[single_df['test_case'] == tc]['scores']:
                try:
                    scores = eval(scores_str)
                    if scores:
                        single_tc_scores.append(max(scores))
                except:
                    pass
                
            if multi_tc_scores:
                multi_scores[tc] = np.mean(multi_tc_scores)
            if single_tc_scores:
                single_scores[tc] = np.mean(single_tc_scores)
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = np.arange(len(test_cases))
        width = 0.35
        
        multi_vals = [multi_scores.get(tc, 0) for tc in test_cases]
        single_vals = [single_scores.get(tc, 0) for tc in test_cases]
        
        rects1 = ax.bar(x - width/2, multi_vals, width, label='Multi-Turn', color='#ff7f0e', alpha=0.8)
        rects2 = ax.bar(x + width/2, single_vals, width, label='Single-Turn', color='#1f77b4', alpha=0.8)
        
        # Add value labels
        for i, v in enumerate(multi_vals):
            ax.text(i - width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
        
        for i, v in enumerate(single_vals):
            ax.text(i + width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Test Case', fontsize=12)
        ax.set_ylabel('Average Best Score (0-1 Scale)', fontsize=12)
        ax.set_title(f'Average Score by Test Case - {model_short}', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(test_cases, rotation=45, ha='right')
        ax.set_ylim(0, 1.0)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(model_dir, f'testcase_scores_{model_short}.png'), dpi=300)
        plt.close()
        
        # Create a similar plot for tactics
        plt.figure(figsize=(14, 10))
        
        # Calculate mean scores per tactic
        multi_tactic_scores = {}
        single_tactic_scores = {}
        
        for tactic in tactics:
            multi_t_scores = []
            for scores_str in multi_df[multi_df['jailbreak_tactic'] == tactic]['scores']:
                try:
                    scores = eval(scores_str)
                    if scores:
                        multi_t_scores.append(max(scores))
                except:
                    pass
            
            single_t_scores = []
            for scores_str in single_df[single_df['jailbreak_tactic'] == tactic]['scores']:
                try:
                    scores = eval(scores_str)
                    if scores:
                        single_t_scores.append(max(scores))
                except:
                    pass
                
            if multi_t_scores:
                multi_tactic_scores[tactic] = np.mean(multi_t_scores)
            if single_t_scores:
                single_tactic_scores[tactic] = np.mean(single_t_scores)
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = np.arange(len(tactics))
        width = 0.35
        
        multi_vals = [multi_tactic_scores.get(t, 0) for t in tactics]
        single_vals = [single_tactic_scores.get(t, 0) for t in tactics]
        
        rects1 = ax.bar(x - width/2, multi_vals, width, label='Multi-Turn', color='#ff7f0e', alpha=0.8)
        rects2 = ax.bar(x + width/2, single_vals, width, label='Single-Turn', color='#1f77b4', alpha=0.8)
        
        # Add value labels
        for i, v in enumerate(multi_vals):
            ax.text(i - width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
        
        for i, v in enumerate(single_vals):
            ax.text(i + width/2, v + 0.02, f'{v:.2f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Jailbreak Tactic', fontsize=12)
        ax.set_ylabel('Average Best Score (0-1 Scale)', fontsize=12)
        ax.set_title(f'Average Score by Tactic - {model_short}', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(tactics, rotation=45, ha='right')
        ax.set_ylim(0, 1.0)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(model_dir, f'tactic_scores_{model_short}.png'), dpi=300)
        plt.close()

if __name__ == "__main__":
    analyze_transformed_6tc() 