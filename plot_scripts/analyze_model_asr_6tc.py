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

def analyze_model_asr_differences(csv_file='strongreject_results_6tc.csv'):
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
    
    # Create output directory
    output_dir = '6tc_analysis_results'
    os.makedirs(output_dir, exist_ok=True)
    
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
    print("\n=== Overall Attack Success Rate (ASR) by Model (6TC Dataset) ===")
    print(f"{'Model':<25} {'Multi-Turn ASR':>15} {'Single-Turn ASR':>20} {'Difference (M-S)':>20}")
    print("-" * 80)
    
    # Also save to file
    with open(os.path.join(output_dir, 'overall_asr_results.txt'), 'w') as f:
        f.write("=== Overall Attack Success Rate (ASR) by Model (6TC Dataset) ===\n")
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
    plt.ylabel('Average ASR (Best Score)', fontsize=12)
    plt.title('Attack Success Rate Comparison Between Models (6TC Dataset)', fontsize=14)
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
        plt.title('Multi-Turn Advantage by Model and Test Category (6TC Dataset)', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'model_testcategory_advantage_heatmap.png'), dpi=300)
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
        plt.title('Multi-Turn Advantage by Model and Jailbreak Tactic (6TC Dataset)', fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'model_tactic_advantage_heatmap.png'), dpi=300)
        plt.close()
        
    # Create model-specific split-cell heatmaps
    create_model_split_cell_heatmaps(df, all_results, output_dir)
        
    print(f"\nAnalysis complete. Results and visualizations saved to {output_dir} directory.")

def create_model_split_cell_heatmaps(df, all_results, output_dir):
    """
    Create split-cell heatmaps for each model comparing multi-turn and single-turn results.
    
    Args:
        df: Original dataframe
        all_results: Dictionary with processed results
        output_dir: Directory to save output files
    """
    # Create a subdirectory for model heatmaps
    model_heatmaps_dir = os.path.join(output_dir, 'model_heatmaps')
    os.makedirs(model_heatmaps_dir, exist_ok=True)
    
    for model_name in all_results:
        if 'multi' not in all_results[model_name] or 'single' not in all_results[model_name]:
            continue
        
        # Get the data for this model
        multi_data = all_results[model_name]['multi']
        single_data = all_results[model_name]['single']
        
        # Find common test cases and tactics
        multi_cases_tactics = set(multi_data.keys())
        single_cases_tactics = set(single_data.keys())
        common_cases_tactics = multi_cases_tactics & single_cases_tactics
        
        if not common_cases_tactics:
            continue
        
        # Extract test cases and tactics
        test_cases = sorted(set(ct[0] for ct in common_cases_tactics))
        tactics = sorted(set(ct[1] for ct in common_cases_tactics))
        
        # Create dataframes for heatmaps
        multi_matrix = np.zeros((len(test_cases), len(tactics)))
        single_matrix = np.zeros((len(test_cases), len(tactics)))
        
        for i, test_case in enumerate(test_cases):
            for j, tactic in enumerate(tactics):
                if (test_case, tactic) in multi_data and (test_case, tactic) in single_data:
                    multi_matrix[i, j] = multi_data[(test_case, tactic)]
                    single_matrix[i, j] = single_data[(test_case, tactic)]
        
        # Create the heatmap
        plt.figure(figsize=(16, 12))
        
        # Create grid layout
        gs = plt.GridSpec(2, 3, width_ratios=[2.0, 20, 0.5], height_ratios=[20, 2.5], 
                         wspace=0.05, hspace=0.05)
        
        # Main heatmap area
        ax_main = plt.subplot(gs[0, 1])
        
        # Set up the plot dimensions
        ax_main.set_xlim(0, len(tactics))
        ax_main.set_ylim(0, len(test_cases))
        
        # Create the split-cell heatmap
        cmap = plt.cm.YlOrRd
        norm = plt.Normalize(0, 1)
        
        # Plot each cell with diagonal split
        for i, test_case in enumerate(test_cases):
            for j, tactic in enumerate(tactics):
                # Get values
                multi_val = multi_matrix[i, j]
                single_val = single_matrix[i, j]
                
                # Create diagonal line
                diag_line = np.array([[j, i], [j+1, i+1]])
                
                # Create triangles
                upper_left = np.array([[j, i], [j+1, i+1], [j, i+1]])
                lower_right = np.array([[j, i], [j+1, i+1], [j+1, i]])
                
                # Get colors
                multi_color = cmap(norm(multi_val))
                single_color = cmap(norm(single_val))
                
                # Draw triangles
                ax_main.add_patch(plt.Polygon(upper_left, color=multi_color, alpha=0.9))
                ax_main.add_patch(plt.Polygon(lower_right, color=single_color, alpha=0.9))
                
                # Draw diagonal line
                ax_main.plot(diag_line[:, 0], diag_line[:, 1], 'k-', linewidth=0.5)
                
                # Add text annotations
                ax_main.text(j + 0.25, i + 0.75, f'M: {multi_val:.2f}', 
                          ha='center', va='center', fontsize=11, color='black')
                ax_main.text(j + 0.75, i + 0.25, f'S: {single_val:.2f}', 
                          ha='center', va='center', fontsize=11, color='black')
        
        # Add gridlines
        for x in range(len(tactics) + 1):
            ax_main.axvline(x, color='black', linewidth=0.5)
        for y in range(len(test_cases) + 1):
            ax_main.axhline(y, color='black', linewidth=0.5)
        
        # Calculate averages
        multi_tactic_avg = np.mean(multi_matrix, axis=0)
        single_tactic_avg = np.mean(single_matrix, axis=0)
        
        multi_testcase_avg = np.mean(multi_matrix, axis=1)
        single_testcase_avg = np.mean(single_matrix, axis=1)
        
        # Add bar chart for tactic averages
        ax_tactic_avg = plt.subplot(gs[1, 1], sharex=ax_main)
        bar_width = 0.35
        x_pos = np.arange(len(tactics)) + 0.5
        
        # Plot bar chart
        ax_tactic_avg.bar(x_pos - bar_width/2, multi_tactic_avg, bar_width, color='#ff7f0e', alpha=0.7, label='Multi')
        ax_tactic_avg.bar(x_pos + bar_width/2, single_tactic_avg, bar_width, color='#1f77b4', alpha=0.7, label='Single')
        
        # Add values
        for i, val in enumerate(multi_tactic_avg):
            ax_tactic_avg.text(x_pos[i] - bar_width/2, val + 0.02, f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        for i, val in enumerate(single_tactic_avg):
            ax_tactic_avg.text(x_pos[i] + bar_width/2, val + 0.02, f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        
        ax_tactic_avg.set_ylim(0, 1.1)
        ax_tactic_avg.legend(loc='upper left', fontsize=8)
        ax_tactic_avg.set_ylabel('Avg Score', fontsize=10)
        
        # Add bar chart for test case averages
        ax_testcase_avg = plt.subplot(gs[0, 0], sharey=ax_main)
        y_pos = np.arange(len(test_cases)) + 0.5
        
        # Plot bar chart
        ax_testcase_avg.barh(y_pos + bar_width/2, multi_testcase_avg, bar_width, color='#ff7f0e', alpha=0.7, label='Multi')
        ax_testcase_avg.barh(y_pos - bar_width/2, single_testcase_avg, bar_width, color='#1f77b4', alpha=0.7, label='Single')
        
        # Add values
        for i, val in enumerate(multi_testcase_avg):
            ax_testcase_avg.text(val + 0.02, y_pos[i] + bar_width/2, f'{val:.2f}', va='center', ha='left', fontsize=8)
        for i, val in enumerate(single_testcase_avg):
            ax_testcase_avg.text(val + 0.02, y_pos[i] - bar_width/2, f'{val:.2f}', va='center', ha='left', fontsize=8)
        
        ax_testcase_avg.set_xlim(0, 1.1)
        ax_testcase_avg.legend(loc='upper left', bbox_to_anchor=(0, 1.05), fontsize=8)
        ax_testcase_avg.set_xlabel('Avg Score', fontsize=10)
        
        # Add empty plot for bottom left
        ax_empty = plt.subplot(gs[1, 0])
        ax_empty.axis('off')
        
        # Add colorbar
        cbar_ax = plt.subplot(gs[0, 2])
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, cax=cbar_ax)
        
        # Set up axis labels and ticks
        ax_main.set_xticks(np.arange(len(tactics)) + 0.5)
        ax_main.set_yticks(np.arange(len(test_cases)) + 0.5)
        ax_main.set_xticklabels([])
        ax_main.set_yticklabels([])
        
        ax_tactic_avg.set_xticks(np.arange(len(tactics)) + 0.5)
        ax_tactic_avg.set_xticklabels(tactics, rotation=45, ha='right', fontsize=9)
        
        ax_testcase_avg.set_yticks(np.arange(len(test_cases)) + 0.5)
        ax_testcase_avg.set_yticklabels(test_cases, fontsize=9)
        
        # Add title
        plt.suptitle(f'Model: {model_name} - Multi-Turn vs Single-Turn Best Score (6TC Dataset)', fontsize=14)
        
        # Save the figure
        plt.savefig(os.path.join(model_heatmaps_dir, f'split_cell_heatmap_{model_name}.png'), 
                    dpi=300, bbox_inches='tight')
        plt.close()

if __name__ == "__main__":
    analyze_model_asr_differences() 