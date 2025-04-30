#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

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

def create_split_cell_heatmap_by_model(df, output_dir, csv_filename, metric='best_score'):
    """
    Create a split-cell heatmap for each model showing success by tactic and test case,
    with separate triangular cells for multi-turn and single-turn results.
    
    Args:
        df: DataFrame containing the data
        output_dir: Directory to save output files
        csv_filename: Name of the source CSV file (for naming output files)
        metric: Either 'success_rate' or 'best_score'
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get unique models
    models = df['target_model'].unique()
    
    # Loop through each model
    for model in models:
        model_df = df[df['target_model'] == model]
        
        # Skip if no data for this model
        if model_df.empty:
            print(f"No data for model: {model}")
            continue
        
        # For file naming, use the model's shortened name
        model_short_name = model.split('/')[-1]
        
        # Filter data for each turn type
        multi_turn_df = model_df[model_df['turn_type'] == 'multi']
        single_turn_df = model_df[model_df['turn_type'] == 'single']
        
        # Skip if data is missing for either turn type
        if multi_turn_df.empty or single_turn_df.empty:
            print(f"Missing data for one turn type for model: {model}")
            continue
        
        # Calculate means for each turn type using the best_score metric
        multi_success_means = multi_turn_df.pivot_table(
            values='scores',
            index='test_case',
            columns='jailbreak_tactic',
            aggfunc=lambda x: np.mean([get_best_score(s) for s in x])
        )
        
        single_success_means = single_turn_df.pivot_table(
            values='scores',
            index='test_case',
            columns='jailbreak_tactic',
            aggfunc=lambda x: np.mean([get_best_score(s) for s in x])
        )
        
        # Find common test cases and tactics between multi and single turn data
        common_test_cases = sorted(set(multi_success_means.index) & set(single_success_means.index))
        common_tactics = sorted(set(multi_success_means.columns) & set(single_success_means.columns))
        
        # Skip if no common data
        if not common_test_cases or not common_tactics:
            print(f"No common test cases/tactics for model: {model}")
            continue
        
        # Filter to only include common test cases and tactics
        multi_success_means = multi_success_means.loc[common_test_cases, common_tactics]
        single_success_means = single_success_means.loc[common_test_cases, common_tactics]
        
        # Calculate average success rates across all test cases for each turn type
        multi_tactic_averages = multi_success_means.mean(axis=0)
        single_tactic_averages = single_success_means.mean(axis=0)
        
        # Calculate average success rates for each test case
        multi_testcase_averages = multi_success_means.mean(axis=1)
        single_testcase_averages = single_success_means.mean(axis=1)
        
        # Create the figure with extra space for averages
        plt.figure(figsize=(14, 12))
        
        # Define subplot layout with better proportions and more height for bar plots
        gs = plt.GridSpec(2, 3, width_ratios=[2.0, 20, 0.5], height_ratios=[20, 2.5], 
                         wspace=0.05, hspace=0.05)
        
        # Main heatmap area
        ax_main = plt.subplot(gs[0, 1])
        
        # Create an empty canvas for our custom heatmap
        all_test_cases = list(multi_success_means.index)
        all_tactics = list(multi_success_means.columns)
        
        ax_main.set_xlim(0, len(all_tactics))
        ax_main.set_ylim(0, len(all_test_cases))
        
        # For each cell, create a split-cell for visualization
        for i, test_case in enumerate(all_test_cases):
            for j, tactic in enumerate(all_tactics):
                # Get values for this cell
                multi_value = multi_success_means.loc[test_case, tactic]
                single_value = single_success_means.loc[test_case, tactic]
                
                # Skip if we somehow have NaN values
                if np.isnan(multi_value) or np.isnan(single_value):
                    continue
                    
                # Using the YlOrRd colormap for all cells
                cmap = plt.cm.YlOrRd
                norm = plt.Normalize(0, 1)  # Range 0-1 for best score
                
                # Create coordinates for the diagonal line
                diag_line = np.array([[j, i], [j+1, i+1]])
                
                # Create polygons for the two triangles (upper left and lower right)
                upper_left_triangle = np.array([[j, i], [j+1, i+1], [j, i+1]])
                lower_right_triangle = np.array([[j, i], [j+1, i+1], [j+1, i]])
                
                # Get colors based on the values
                multi_color = cmap(norm(multi_value))
                single_color = cmap(norm(single_value))
                
                # Draw the triangles
                upper_left = plt.Polygon(upper_left_triangle, color=multi_color, alpha=0.9)
                lower_right = plt.Polygon(lower_right_triangle, color=single_color, alpha=0.9)
                
                ax_main.add_patch(upper_left)
                ax_main.add_patch(lower_right)
                
                # Draw the diagonal line
                plt.plot(diag_line[:, 0], diag_line[:, 1], 'k-', linewidth=0.5)
                
                # Add text annotations for multi-turn (top) with M: prefix
                text_multi = f'M: {multi_value:.2f}'
                text_color_multi = 'black'  # Always black for best_score
                
                # Position text in upper left triangle
                ax_main.text(j + 0.25, i + 0.75, text_multi,
                        ha='center', va='center', color=text_color_multi, fontsize=14)
                
                # Add text annotations for single-turn (bottom) with S: prefix
                text_single = f'S: {single_value:.2f}'
                text_color_single = 'black'  # Always black for best_score
                
                # Position text in lower right triangle
                ax_main.text(j + 0.75, i + 0.25, text_single,
                        ha='center', va='center', color=text_color_single, fontsize=14)
        
        # Add gridlines to separate cells
        for x in range(len(all_tactics) + 1):
            plt.axvline(x, color='black', linewidth=0.5)
        for y in range(len(all_test_cases) + 1):
            plt.axhline(y, color='black', linewidth=0.5)
        
        # Set up the axis ticks but hide all labels for main heatmap
        ax_main.set_xticks(np.arange(len(all_tactics)) + 0.5)
        ax_main.set_yticks(np.arange(len(all_test_cases)) + 0.5)
        ax_main.set_xticklabels([])  # Explicitly remove x-axis labels for main heatmap
        ax_main.set_yticklabels([])  # Explicitly remove y-axis labels for main heatmap
        
        # Create tactic averages bar at bottom - exact same width as main heatmap
        ax_tactic_avg = plt.subplot(gs[1, 1], sharex=ax_main)
        
        # Create bar pairs for multi and single turn averages
        x_pos = np.arange(len(all_tactics)) + 0.5  # Center bars on tactic positions
        bar_width = 0.35  # Both types of data exist for all cells
        
        # Plot bars for tactic averages
        for i, tactic in enumerate(all_tactics):
            multi_val = multi_tactic_averages[tactic]
            single_val = single_tactic_averages[tactic]
            
            # Multi-turn bar (left position)
            bar_pos_multi = x_pos[i] - bar_width/2
            ax_tactic_avg.bar(bar_pos_multi, multi_val, bar_width, color='#ff7f0e', alpha=0.7)
            ax_tactic_avg.text(bar_pos_multi, multi_val + 0.02, f'{multi_val:.2f}', 
                         ha='center', va='bottom', fontsize=9)
            
            # Single-turn bar (right position)
            bar_pos_single = x_pos[i] + bar_width/2
            ax_tactic_avg.bar(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
            ax_tactic_avg.text(bar_pos_single, single_val + 0.02, f'{single_val:.2f}', 
                         ha='center', va='bottom', fontsize=9)
        
        # Create legend for bottom average bars
        handles = [
            plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
            plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
        ]
        labels = ['Multi', 'Single']
        ax_tactic_avg.legend(handles, labels, loc='upper left', fontsize=9)
        
        # Set y-axis limits for best score
        ax_tactic_avg.set_ylim(0, 1.0)
        metric_label = "Best Score"
        
        ax_tactic_avg.set_ylabel(metric_label, fontsize=11)
        ax_tactic_avg.set_yticks([])
        
        ax_tactic_avg.set_xticklabels(all_tactics, fontsize=11)
        
        # Create test case averages column on left
        ax_testcase_avg = plt.subplot(gs[0, 0], sharey=ax_main)
        
        # Create bar pairs for multi and single turn test case averages
        y_pos = np.arange(len(all_test_cases)) + 0.5  # Center bars on test case positions
        
        # Plot bars for test case averages (horizontal)
        for i, test_case in enumerate(all_test_cases):
            multi_val = multi_testcase_averages[test_case]
            single_val = single_testcase_averages[test_case]
            
            # Multi-turn bar (top position)
            bar_pos_multi = y_pos[i] + bar_width/2
            ax_testcase_avg.barh(bar_pos_multi, multi_val, bar_width, color='#ff7f0e', alpha=0.7)
            ax_testcase_avg.text(multi_val + 0.02, bar_pos_multi, f'{multi_val:.2f}', 
                           ha='left', va='center', fontsize=10)
            
            # Single-turn bar (bottom position)
            bar_pos_single = y_pos[i] - bar_width/2
            ax_testcase_avg.barh(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
            ax_testcase_avg.text(single_val + 0.02, bar_pos_single, f'{single_val:.2f}', 
                           ha='left', va='center', fontsize=10)
        
        # Create legend for left average bars
        handles = [
            plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
            plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
        ]
        labels = ['Multi', 'Single']
        ax_testcase_avg.legend(handles, labels, loc='upper left', bbox_to_anchor=(0, 1.06), fontsize=9)
        
        # Set x-axis limits for best score
        ax_testcase_avg.set_xlim(0, 1.0)
        
        ax_testcase_avg.set_xlabel(metric_label, fontsize=11)
        ax_testcase_avg.set_xticks([])
        
        # Set test case labels only on the left side
        ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=11)
        
        # Add empty plot for the bottom left square
        ax_empty = plt.subplot(gs[1, 0])
        ax_empty.axis('off')
        
        # Add colorbar
        cbar_ax = plt.subplot(gs[0, 2])
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, cax=cbar_ax)
        cbar.set_label(metric_label, fontsize=12)
        cbar.ax.tick_params(labelsize=14)
        
        # CRITICAL: Explicitly remove ticks and labels from main heatmap again
        ax_main.set_xticklabels([])
        ax_main.set_yticklabels([])
        plt.setp(ax_main.get_xticklabels(), visible=False)
        plt.setp(ax_main.get_yticklabels(), visible=False)
        
        # Make sure only tactic_avg has x-labels and only testcase_avg has y-labels
        plt.setp(ax_tactic_avg.get_xticklabels(), visible=True)
        plt.setp(ax_testcase_avg.get_yticklabels(), visible=True)
        
        # Add title 
        title = f'Split-Cell Best Score by Tactic and Test Case\n{model_short_name}'
        plt.suptitle(title, fontsize=16)
        
        # For tactic averages (bottom plot)
        ax_tactic_avg.tick_params(axis='x', which='both', labelbottom=True)
        ax_tactic_avg.set_xticks(np.arange(len(all_tactics)) + 0.5)
        ax_tactic_avg.set_xticklabels(all_tactics, fontsize=14, rotation=45, ha='right')
        
        # For test case averages (left plot)
        ax_testcase_avg.tick_params(axis='y', which='both', labelleft=True)
        ax_testcase_avg.set_yticks(np.arange(len(all_test_cases)) + 0.5)
        ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=14)
        
        # Explicitly turn off ticks on other axes to prevent override
        ax_main.tick_params(axis='both', which='both', labelbottom=False, labelleft=False)
        
        # Add a bit more padding to ensure labels aren't cut off
        plt.tight_layout(rect=[0, 0, 0.95, 0.95])  # Leave space for the title
        
        # Save the figure
        base_filename = Path(csv_filename).stem
        output_path = os.path.join(
            output_dir, 
            f"success_by_tactic_test_from_{base_filename}_{model_short_name}_{metric}.png"
        )
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved split-cell heatmap for {model_short_name} to {output_path}")

def main():
    """Main function to parse arguments and run the script."""
    parser = argparse.ArgumentParser(description='Create model-specific split-cell heatmaps from CSV data')
    parser.add_argument('--csv', type=str, default='results_strongreject_transformed.csv',
                        help='Name of the CSV file in the csv_results directory')
    parser.add_argument('--metric', type=str, choices=['best_score'], default='best_score',
                        help='Metric to use for analysis')
    parser.add_argument('--output-dir', type=str, default='plot_outputs_model',
                        help='Directory to save plots')
    
    args = parser.parse_args()
    
    # Load the CSV file
    csv_path = os.path.join('csv_results', args.csv)
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    df = pd.read_csv(csv_path)
    
    # Create the heatmaps
    create_split_cell_heatmap_by_model(df, args.output_dir, args.csv, args.metric)
    
    print(f"All plots saved to {args.output_dir}")

if __name__ == "__main__":
    main() 