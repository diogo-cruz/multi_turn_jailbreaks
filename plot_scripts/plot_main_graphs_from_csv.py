#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter
import argparse
import os

# Define model sizes (in billions of parameters)
MODEL_SIZES = {
    "gpt-4o-mini-2024-07-18": 8,  # Approximate size
    "meta-llama/llama-3.1-8b-instruct": 8,
    "meta-llama/llama-3.1-70b-instruct": 70,
    "meta-llama/llama-3.1-405b-instruct": 405,
    "meta-llama/llama-3.2-1b-instruct": 1,
    "meta-llama/llama-3.2-3b-instruct": 3,
    "meta-llama/llama-3.3-70b-instruct": 70
}



def create_last_round_split_cell_heatmap(df, output_dir, output_filename, target_model=None):
    """
    Create a refined heatmap using the average of the last round's score instead of goal_achieved.
    Similar to create_refined_split_cell_heatmap but using different metrics.
    """
    # Filter by target_model if specified
    if target_model is not None:
        df = df[df['target_model'] == target_model]
        if df.empty:
            print(f"Warning: No data found for target model '{target_model}'")
            return
        # Add model info to filename unless already present
        if target_model not in output_filename:
            name_parts = output_filename.split('.')
            output_filename = f"{name_parts[0]}_{target_model.split('/')[-1]}.{name_parts[1]}"
    
    # Filter data for each turn type
    multi_turn_df = df[df['turn_type'] == 'multi']
    single_turn_df = df[df['turn_type'] == 'single']
    
    # Function to extract the last score from the scores list
    def extract_last_score(scores_str):
        try:
            # Parse the string representation of the list
            scores_list = eval(scores_str)
            # Return the last score if the list is not empty
            return scores_list[-1] if scores_list else 0
        except:
            return 0
    
    # Add last_score column to each dataframe
    multi_turn_df = multi_turn_df.copy()
    single_turn_df = single_turn_df.copy()
    
    multi_turn_df['last_score'] = multi_turn_df['scores'].apply(extract_last_score)
    single_turn_df['last_score'] = single_turn_df['scores'].apply(extract_last_score)
    
    # Calculate mean last_score for each turn type
    multi_last_score_means = multi_turn_df.pivot_table(
        values='last_score',  # Use last_score instead of goal_achieved
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    )
    
    single_last_score_means = single_turn_df.pivot_table(
        values='last_score',  # Use last_score instead of goal_achieved
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    )
    
    # Find tactics that have both multi and single turn data
    valid_combinations = []
    for test_case in multi_last_score_means.index:
        for tactic in multi_last_score_means.columns:
            # Check if this combination exists in both multi and single turn data
            has_multi = (test_case in multi_last_score_means.index and 
                        tactic in multi_last_score_means.columns and 
                        not pd.isna(multi_last_score_means.loc[test_case, tactic]))
            
            has_single = (test_case in single_last_score_means.index and 
                         tactic in single_last_score_means.columns and 
                         not pd.isna(single_last_score_means.loc[test_case, tactic]))
            
            if has_multi and has_single:
                valid_combinations.append((test_case, tactic))
    
    # If no valid combinations, print warning and return
    if not valid_combinations:
        print("Warning: No test case/tactic combinations found with both multi-turn and single-turn data.")
        return
    
    # Get unique test cases and tactics that have both types of data
    valid_test_cases = sorted(set(combo[0] for combo in valid_combinations))
    valid_tactics = sorted(set(combo[1] for combo in valid_combinations))
    
    # Filter the original dataframe to only include these combinations
    filtered_df = df[
        (df['test_case'].isin(valid_test_cases)) & 
        (df['jailbreak_tactic'].isin(valid_tactics))
    ]
    
    # Create filtered dataframes with last_score
    filtered_multi_df = filtered_df[filtered_df['turn_type'] == 'multi'].copy()
    filtered_single_df = filtered_df[filtered_df['turn_type'] == 'single'].copy()
    
    filtered_multi_df['last_score'] = filtered_multi_df['scores'].apply(extract_last_score)
    filtered_single_df['last_score'] = filtered_single_df['scores'].apply(extract_last_score)
    
    # Recalculate means with filtered data
    multi_last_score_means = filtered_multi_df.pivot_table(
        values='last_score',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    )
    
    single_last_score_means = filtered_single_df.pivot_table(
        values='last_score',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    )
    
    # Calculate average last_scores across all test cases for each turn type
    multi_tactic_averages = multi_last_score_means.mean(axis=0)
    single_tactic_averages = single_last_score_means.mean(axis=0)
    
    # Calculate average last_scores for each test case
    multi_testcase_averages = multi_last_score_means.mean(axis=1)
    single_testcase_averages = single_last_score_means.mean(axis=1)
    
    # Create the figure with extra space for averages
    plt.figure(figsize=(14, 12))
    
    # Define subplot layout with better proportions and more height for bar plots
    gs = plt.GridSpec(2, 3, width_ratios=[2.0, 20, 0.5], height_ratios=[20, 2.5], 
                     wspace=0.05, hspace=0.05)
    
    # Main heatmap area
    ax_main = plt.subplot(gs[0, 1])
    
    # Create an empty canvas for our custom heatmap
    all_test_cases = list(multi_last_score_means.index)
    all_tactics = list(multi_last_score_means.columns)
    
    ax_main.set_xlim(0, len(all_tactics))
    ax_main.set_ylim(0, len(all_test_cases))
    
    # For each cell, create a split-cell for visualization
    for i, test_case in enumerate(all_test_cases):
        for j, tactic in enumerate(all_tactics):
            # Get values for this cell
            multi_value = multi_last_score_means.loc[test_case, tactic]
            single_value = single_last_score_means.loc[test_case, tactic]
            
            # Skip if we somehow have NaN values
            if np.isnan(multi_value) or np.isnan(single_value):
                continue
                
            # Using a blue-based colormap since we're dealing with scores 0-10 instead of percentages
            cmap = plt.cm.YlGnBu  # Changed colormap to better suit score range
            norm = plt.Normalize(0, 10)  # Score range is 0-10 instead of 0-100
            
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
            text_multi = f'M: {multi_value:.1f}'
            
            # Text color based on background (adjust thresholds for 0-10 scale)
            text_color_multi = 'white' if multi_value > 5 else 'black'
            
            # Position text in upper left triangle
            ax_main.text(j + 0.25, i + 0.75, text_multi,
                    ha='center', va='center', color=text_color_multi, fontsize=14)  # Increased font size
        
            # Add text annotations for single-turn (bottom) with S: prefix
            text_single = f'S: {single_value:.1f}'
            
            # Text color based on background (adjust thresholds for 0-10 scale)
            text_color_single = 'white' if single_value > 5 else 'black'
            
            # Position text in lower right triangle
            ax_main.text(j + 0.75, i + 0.25, text_single,
                    ha='center', va='center', color=text_color_single, fontsize=14)  # Increased font size
    
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
        ax_tactic_avg.text(bar_pos_multi, multi_val + 0.2, f'{multi_val:.1f}', 
                     ha='center', va='bottom', fontsize=10)
        
        # Single-turn bar (right position)
        bar_pos_single = x_pos[i] + bar_width/2
        ax_tactic_avg.bar(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
        ax_tactic_avg.text(bar_pos_single, single_val + 0.2, f'{single_val:.1f}', 
                     ha='center', va='bottom', fontsize=10)
    
    # Create legend for bottom average bars
    handles = [
        plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
        plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
    ]
    labels = ['Multi', 'Single']
    ax_tactic_avg.legend(handles, labels, loc='upper left', fontsize=10)
    
    ax_tactic_avg.set_ylim(0, 12)  # Set y limit to 12 for 0-10 scale scores with some padding
    ax_tactic_avg.set_ylabel('Avg Last Score', fontsize=12)
    ax_tactic_avg.set_yticks([])
    
    ax_tactic_avg.set_xticklabels(all_tactics, fontsize=14)  # Increased font size
    
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
        ax_testcase_avg.text(multi_val + 0.2, bar_pos_multi, f'{multi_val:.1f}', 
                       ha='left', va='center', fontsize=10)
        
        # Single-turn bar (bottom position)
        bar_pos_single = y_pos[i] - bar_width/2
        ax_testcase_avg.barh(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
        ax_testcase_avg.text(single_val + 0.2, bar_pos_single, f'{single_val:.1f}', 
                       ha='left', va='center', fontsize=10)
    
    # Create legend for left average bars
    handles = [
        plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
        plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
    ]
    labels = ['Multi', 'Single']
    ax_testcase_avg.legend(handles, labels, loc='upper left', bbox_to_anchor=(0, 1.06), fontsize=10)
    
    ax_testcase_avg.set_xlim(0, 15)  # Set x limit to 15 for 0-10 scale scores with some padding
    ax_testcase_avg.set_xlabel('Avg Last Score', fontsize=12)
    ax_testcase_avg.set_xticks([])
    
    # Set test case labels only on the left side
    ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=14)  # Increased font size
    
    # Add empty plot for the bottom left square
    ax_empty = plt.subplot(gs[1, 0])
    ax_empty.axis('off')
    
    # Add colorbar
    cbar_ax = plt.subplot(gs[0, 2])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Last Round Score (0-10)', fontsize=12)
    
    # CRITICAL: Explicitly remove ticks and labels from main heatmap again
    ax_main.set_xticklabels([])
    ax_main.set_yticklabels([])
    plt.setp(ax_main.get_xticklabels(), visible=False)
    plt.setp(ax_main.get_yticklabels(), visible=False)
    
    # Make sure only tactic_avg has x-labels and only testcase_avg has y-labels
    plt.setp(ax_tactic_avg.get_xticklabels(), visible=True)
    plt.setp(ax_testcase_avg.get_yticklabels(), visible=True)
    
    # Add title
    if target_model is not None:
        plt.suptitle(f'Split-Cell Last Round Score (0-10) by Tactic and Test Case for {target_model}', fontsize=16)
    else:
        plt.suptitle('Split-Cell Last Round Score (0-10) by Tactic and Test Case', fontsize=16)
    
    # For tactic averages (bottom plot)
    ax_tactic_avg.tick_params(axis='x', which='both', labelbottom=True)
    ax_tactic_avg.set_xticks(np.arange(len(all_tactics)) + 0.5)
    ax_tactic_avg.set_xticklabels(all_tactics, fontsize=14)  # Increased font size

    # For test case averages (left plot)
    ax_testcase_avg.tick_params(axis='y', which='both', labelleft=True)
    ax_testcase_avg.set_yticks(np.arange(len(all_test_cases)) + 0.5)
    ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=14)  # Increased font size

    # Explicitly turn off ticks on other axes to prevent override
    ax_main.tick_params(axis='both', which='both', labelbottom=False, labelleft=False)

    # Add a bit more padding to ensure labels aren't cut off
    plt.tight_layout(rect=[0, 0.05, 0.95, 0.95])
    
    # Save the figure
    output_path = output_dir/output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved last round score split-cell heatmap to {output_filename}")
    print(f"Included {len(valid_tactics)} tactics and {len(valid_test_cases)} test cases with data from both turn types")




def create_refined_split_cell_heatmap(df, output_dir, output_filename, target_model=None):
    """
    Create a refined heatmap that only includes tactics and test cases
    where both multi-turn and single-turn data are available.
    """
    # Filter by target_model if specified
    if target_model is not None:
        df = df[df['target_model'] == target_model]
        if df.empty:
            print(f"Warning: No data found for target model '{target_model}'")
            return
        # Add model info to filename unless already present
        if target_model not in output_filename:
            name_parts = output_filename.split('.')
            output_filename = f"{name_parts[0]}_{target_model.split('/')[-1]}.{name_parts[1]}"
            
    # Filter data for each turn type
    multi_turn_df = df[df['turn_type'] == 'multi']
    single_turn_df = df[df['turn_type'] == 'single']
    
    # Calculate mean success rates for each turn type
    multi_success_means = multi_turn_df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
    single_success_means = single_turn_df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
    # Find tactics that have both multi and single turn data
    valid_combinations = []
    for test_case in multi_success_means.index:
        for tactic in multi_success_means.columns:
            # Check if this combination exists in both multi and single turn data
            has_multi = (test_case in multi_success_means.index and 
                        tactic in multi_success_means.columns and 
                        not pd.isna(multi_success_means.loc[test_case, tactic]))
            
            has_single = (test_case in single_success_means.index and 
                         tactic in single_success_means.columns and 
                         not pd.isna(single_success_means.loc[test_case, tactic]))
            
            if has_multi and has_single:
                valid_combinations.append((test_case, tactic))
    
    # If no valid combinations, print warning and return
    if not valid_combinations:
        print("Warning: No test case/tactic combinations found with both multi-turn and single-turn data.")
        return
    
    # Get unique test cases and tactics that have both types of data
    valid_test_cases = sorted(set(combo[0] for combo in valid_combinations))
    valid_tactics = sorted(set(combo[1] for combo in valid_combinations))
    
    # Filter the original dataframe to only include these combinations
    filtered_df = df[
        (df['test_case'].isin(valid_test_cases)) & 
        (df['jailbreak_tactic'].isin(valid_tactics))
    ]
    
    # Recalculate means with filtered data
    filtered_multi_df = filtered_df[filtered_df['turn_type'] == 'multi']
    filtered_single_df = filtered_df[filtered_df['turn_type'] == 'single']
    
    multi_success_means = filtered_multi_df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
    single_success_means = filtered_single_df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
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
    
    # For each cell, create a split-cell since we've filtered to only include
    # combinations with both data types
    for i, test_case in enumerate(all_test_cases):
        for j, tactic in enumerate(all_tactics):
            # Get values for this cell
            multi_value = multi_success_means.loc[test_case, tactic]
            single_value = single_success_means.loc[test_case, tactic]
            
            # Skip if we somehow have NaN values (shouldn't happen due to filtering)
            if np.isnan(multi_value) or np.isnan(single_value):
                continue
                
            # Using the YlOrRd colormap for all cells
            cmap = plt.cm.YlOrRd
            norm = plt.Normalize(0, 100)
            
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
            text_multi = f'M: {multi_value:.1f}'
            
            # Text color based on background
            text_color_multi = 'white' if multi_value > 50 else 'black'
            
            # Position text in upper left triangle
            ax_main.text(j + 0.25, i + 0.75, text_multi,
                    ha='center', va='center', color=text_color_multi, fontsize=14)
        
            # Add text annotations for single-turn (bottom) with S: prefix
            text_single = f'S: {single_value:.1f}'
            
            # Text color based on background
            text_color_single = 'white' if single_value > 50 else 'black'
            
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
        ax_tactic_avg.text(bar_pos_multi, multi_val + 2, f'{multi_val:.1f}', 
                     ha='center', va='bottom', fontsize=9)
        
        # Single-turn bar (right position)
        bar_pos_single = x_pos[i] + bar_width/2
        ax_tactic_avg.bar(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
        ax_tactic_avg.text(bar_pos_single, single_val + 2, f'{single_val:.1f}', 
                     ha='center', va='bottom', fontsize=9)
    
    # Create legend for bottom average bars
    handles = [
        plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
        plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
    ]
    labels = ['Multi', 'Single']
    ax_tactic_avg.legend(handles, labels, loc='upper left', fontsize=9)
    
    ax_tactic_avg.set_ylim(0, 120)  # Increased height to prevent number cutoff
    ax_tactic_avg.set_ylabel('ASR(%)', fontsize=11)
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
        ax_testcase_avg.text(multi_val + 2, bar_pos_multi, f'{multi_val:.1f}', 
                       ha='left', va='center', fontsize=9)
        
        # Single-turn bar (bottom position)
        bar_pos_single = y_pos[i] - bar_width/2
        ax_testcase_avg.barh(bar_pos_single, single_val, bar_width, color='#1f77b4', alpha=0.7)
        ax_testcase_avg.text(single_val + 2, bar_pos_single, f'{single_val:.1f}', 
                       ha='left', va='center', fontsize=9)
    
    # Create legend for left average bars
    handles = [
        plt.Rectangle((0,0), 1, 1, color='#ff7f0e', alpha=0.7),
        plt.Rectangle((0,0), 1, 1, color='#1f77b4', alpha=0.7)
    ]
    labels = ['Multi', 'Single']
    ax_testcase_avg.legend(handles, labels, loc='upper left', bbox_to_anchor=(0, 1.06), fontsize=9)
    
    ax_testcase_avg.set_xlim(0, 150)  # Increased width to prevent number cutoff
    ax_testcase_avg.set_xlabel('ASR(%)', fontsize=11)
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
    cbar.set_label('Success Rate (%)', fontsize=12)
    
    # CRITICAL: Explicitly remove ticks and labels from main heatmap again
    ax_main.set_xticklabels([])
    ax_main.set_yticklabels([])
    plt.setp(ax_main.get_xticklabels(), visible=False)
    plt.setp(ax_main.get_yticklabels(), visible=False)
    
    # Make sure only tactic_avg has x-labels and only testcase_avg has y-labels
    plt.setp(ax_tactic_avg.get_xticklabels(), visible=True)
    plt.setp(ax_testcase_avg.get_yticklabels(), visible=True)
    
    # Add title
    if target_model is not None:
        plt.suptitle(f'Split-Cell Success Rate (%) by Tactic and Test Case for {target_model}', fontsize=16)
    else:
        plt.suptitle('Split-Cell Success Rate (%) by Tactic and Test Case', fontsize=16)
    
    
    # After creating all the plots but before plt.tight_layout()

    # For tactic averages (bottom plot)
    ax_tactic_avg.tick_params(axis='x', which='both', labelbottom=True)
    ax_tactic_avg.set_xticks(np.arange(len(all_tactics)) + 0.5)
    ax_tactic_avg.set_xticklabels(all_tactics, fontsize=11)

    # For test case averages (left plot)
    ax_testcase_avg.tick_params(axis='y', which='both', labelleft=True)
    ax_testcase_avg.set_yticks(np.arange(len(all_test_cases)) + 0.5)
    ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=11)

    # Explicitly turn off ticks on other axes to prevent override
    ax_main.tick_params(axis='both', which='both', labelbottom=False, labelleft=False)

    # Add a bit more padding to ensure labels aren't cut off
    plt.tight_layout(rect=[0, 0.05, 0.95, 0.95])  # Increased bottom padding
    
    
    # Adjust layout
    # plt.tight_layout(rect=[0, 0, 0.95, 0.95])
    
    # Save the figure
    output_path = output_dir/output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved refined split-cell heatmap (filtered to only show data with both types) to {output_filename}")
    print(f"Included {len(valid_tactics)} tactics and {len(valid_test_cases)} test cases with data from both turn types")



def create_success_heatmap(df, output_dir, output_filename, turn_type, target_model=None, version=1):
    """
    Create a heatmap showing success rate by jailbreak tactic and test case
    with average success rates for each tactic and test case
    """
    # Filter by target_model if specified
    if target_model is not None:
        df = df[df['target_model'] == target_model]
        if df.empty:
            print(f"Warning: No data found for target model '{target_model}'")
            return
        # Add model info to filename unless already present
        if target_model not in output_filename:
            name_parts = output_filename.split('.')
            output_filename = f"{name_parts[0]}_{target_model.split('/')[-1]}.{name_parts[1]}"
            
    # Calculate mean success rates
    success_means = df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
    # Calculate standard deviations
    success_stds = df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc=lambda x: x.std(ddof=0) if len(x) > 1 else 0 
    ) * 100
    
    # Calculate sample sizes
    sample_sizes = df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='count'
    )
    
    # Calculate average success rates for each tactic (column averages)
    tactic_averages = success_means.mean(axis=0)
    
    # Calculate standard deviations for tactic averages
    tactic_stds = success_means.std(axis=0)
    
    # Calculate total sample sizes for tactic averages
    tactic_samples = sample_sizes.sum(axis=0)
    
    # Calculate average success rates for each test case (row averages)
    testcase_averages = success_means.mean(axis=1)
    
    # Calculate standard deviations for test case averages
    testcase_stds = success_means.std(axis=1)
    
    # Calculate total sample sizes for test case averages
    testcase_samples = sample_sizes.sum(axis=1)
    
    all_test_cases = list(success_means.index)
    all_tactics = list(success_means.columns)
    
    # Create the figure with extra space for averages
    plt.figure(figsize=(18, 16))
    
    # Define subplot layout to accommodate averages
    # Using 3 columns: [avg column, main heatmap, colorbar space]
    if version == 1:
        gs = plt.GridSpec(2, 3, width_ratios=[2, 20, 0.5], height_ratios=[20, 1], 
                     wspace=0.05, hspace=0.05)
    elif version == 2:
        gs = plt.GridSpec(2, 3, width_ratios=[5, 15, 1], height_ratios=[15, 5], 
                        wspace=0.1, hspace=0.1)
        content_label_size = 45
        label_size = 48
        graph_label_size = 30
        ylimit=120
    
    # Main heatmap
    ax_main = plt.subplot(gs[0, 1])
    
    # Create heatmap with mean values
    hm = sns.heatmap(success_means, annot=False, fmt='.1f', cmap='YlOrRd', 
               vmin=0, vmax=100, ax=ax_main, cbar=False)
    
    # Add text annotations with mean and std (n=sample_size)
    for i in range(len(success_means.index)):
        for j in range(len(success_means.columns)):
            mean = success_means.iloc[i, j]
            std = success_stds.iloc[i, j]
            n = sample_sizes.iloc[i, j]
            if not pd.isna(mean):
                # Format text with standard deviation if available
                if pd.isna(std) or std == 0:
                    text = f'{mean:.1f}\n(n={int(n)})'
                else:
                    text = f'{mean:.1f}±{std:.1f}\n(n={int(n)})'
                
                # Calculate text color based on cell color
                text_color = 'white' if mean > 50 else 'black'
                
                if version == 1:
                    ax_main.text(j + 0.5, i + 0.5, text,
                        ha='center', va='center', color=text_color, fontsize=14)
                elif version == 2:
                    continue
                    # ax_main.text(j + 0.5, i + 0.5, text,
                    #     ha='center', va='center', color=text_color, fontsize=14)
    
    if version == 1:
        # Create heatmap for tactic averages (bottom row)
        ax_tactic_avg = plt.subplot(gs[1, 1], sharex=ax_main)
        tactic_avg_df = pd.DataFrame([tactic_averages]).rename(index={0: 'Avg'})
        sns.heatmap(tactic_avg_df, annot=False, fmt='.1f', cmap='YlOrRd',
                vmin=0, vmax=100, ax=ax_tactic_avg, cbar=False)
                
        # Add text annotations with mean, std, and sample size
        for j in range(len(tactic_averages)):
            mean = tactic_averages.iloc[j]
            std = tactic_stds.iloc[j]
            n = tactic_samples.iloc[j]
            
            # Format text with standard deviation and sample size
            text = f'{mean:.1f}±{std:.1f}\n(n={int(n)})'
            
            # Calculate text color based on cell color
            text_color = 'white' if mean > 50 else 'black'
            
            ax_tactic_avg.text(j + 0.5, 0.5, text,
                    ha='center', va='center', color=text_color)
        
        ax_tactic_avg.set_xlabel('Jailbreak Tactic', fontsize=16)
        ax_tactic_avg.set_ylabel('Avg', rotation=0, fontsize=16)
        
    elif version == 2:
        # Create heatmap for tactic averages (bottom row)
        ax_tactic_avg = plt.subplot(gs[1, 1], sharex=ax_main)
        
        # Create bar pairs for multi and single turn averages
        x_pos = np.arange(len(all_tactics)) + 0.5  # Center bars on tactic positions
        bar_width = 0.6  # Both types of data exist for all cells
        
        # Plot bars for tactic averages
        for i, tactic in enumerate(all_tactics):
            val = tactic_averages[tactic]
            
            # bar 
            bar_pos_multi = x_pos[i]
            ax_tactic_avg.bar(bar_pos_multi, val, bar_width, color='#ff7f0e', alpha=0.7)
            ax_tactic_avg.text(bar_pos_multi, val + 2, f'{val:.1f}', 
                        ha='center', va='bottom', fontsize=graph_label_size)
        
        ax_tactic_avg.set_ylim(0, ylimit)  # Increased height to prevent number cutoff
        
        ax_tactic_avg.set_xlabel('Jailbreak Tactic', fontsize=label_size)
        ax_tactic_avg.set_ylabel('ASR(%)', fontsize=label_size)
        ax_tactic_avg.set_yticks([])
        
        ax_tactic_avg.set_xticklabels(all_tactics, fontsize=content_label_size, rotation=45, ha='right')
    
    
    if version == 1:
        # Create heatmap for test case averages (left column)
        ax_testcase_avg = plt.subplot(gs[0, 0], sharey=ax_main)
        testcase_avg_df = pd.DataFrame(testcase_averages).rename(columns={0: 'Avg'})
        sns.heatmap(testcase_avg_df, annot=False, fmt='.1f', cmap='YlOrRd',
                vmin=0, vmax=100, ax=ax_testcase_avg, cbar=False)
                
        # Add text annotations with mean, std, and sample size
        for i in range(len(testcase_averages)):
            mean = testcase_averages.iloc[i]
            std = testcase_stds.iloc[i]
            n = testcase_samples.iloc[i]
            
            # Format text with standard deviation and sample size
            text = f'{mean:.1f}±{std:.1f}\n(n={int(n)})'
            
            # Calculate text color based on cell color
            text_color = 'white' if mean > 50 else 'black'
            
            ax_testcase_avg.text(0.5, i + 0.5, text,
                    ha='center', va='center', color=text_color)
    elif version == 2:
        # Create bar
        ax_testcase_avg = plt.subplot(gs[0, 0], sharey=ax_main)
        y_pos = np.arange(len(all_test_cases)) + 0.5  # Center bars on test case positions
        
        # Plot bars for test case averages (horizontal)
        for i, test_case in enumerate(all_test_cases):
            val = testcase_averages[test_case]
            
            # Multi-turn bar (top position)
            bar_pos_multi = y_pos[i]
            ax_testcase_avg.barh(bar_pos_multi, val, bar_width, color='#ff7f0e', alpha=0.7)
            ax_testcase_avg.text(val + 2, bar_pos_multi, f'{val:.1f}', 
                        ha='left', va='center', fontsize=graph_label_size)
        
        ax_testcase_avg.set_xlim(0, ylimit)  # Increased width to prevent number cutoff
        ax_testcase_avg.set_xlabel('ASR(%)', fontsize=label_size)
        ax_testcase_avg.set_ylabel('Test Case', fontsize=label_size)
        ax_testcase_avg.set_xticks([])
        
        # Set test case labels only on the left side
        ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=content_label_size)
        
    
    # Add empty plot for the bottom left square
    ax_empty = plt.subplot(gs[1, 0])
    ax_empty.axis('off')
    
    # Add colorbar to the main heatmap
    cbar_ax = plt.subplot(gs[0, 2])
    cbar = plt.colorbar(hm.get_children()[0], cax=cbar_ax)
    cbar.set_label('Success Rate (%)', fontsize=label_size)
    cbar.ax.tick_params(labelsize=content_label_size)
    
    # Add title and labels for main plot
    if version == 1:
        if target_model is not None:
            plt.suptitle(f'Success Rate (%) by Tactic and Test Case for {target_model} ({turn_type})', fontsize=16)
        else:
            plt.suptitle(f'Success Rate (%) by Tactic and Test Case ({turn_type})', fontsize=16)
    ax_main.set_xlabel('')
    ax_main.set_ylabel('')  # Remove duplicate y-axis label
    
    # Set the y-axis label only on the averages plot since it's on the left now
    # ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=11)
    # ax_tactic_avg.set_xticklabels(all_tactics, fontsize=11)
    # Rotate x-axis labels for better readability
    # plt.setp(ax_main.get_xticklabels(), rotation=45, ha='right')
    
    # Fix the duplicate axis labels
    plt.setp(ax_testcase_avg.get_yticklabels(), visible=True)  # Keep left labels visible
    # plt.setp(ax_main.get_yticklabels(), visible=False)  # Hide main heatmap y labels
    plt.setp(ax_tactic_avg.get_yticklabels(), visible=False)  # Hide bottom avg y labels
    
    # Fix the duplicate x-axis labels
    plt.setp(ax_tactic_avg.get_xticklabels(), visible=True)  # Keep bottom x labels visible
    # plt.setp(ax_main.get_xticklabels(), visible=False)  # Hide main heatmap x labels
    
    ax_main.set_xticklabels([])
    ax_main.set_yticklabels([])
    plt.setp(ax_main.get_xticklabels(), visible=False)
    plt.setp(ax_main.get_yticklabels(), visible=False)
    
    # For tactic averages (bottom plot)
    ax_tactic_avg.tick_params(axis='x', which='both', labelbottom=True)
    ax_tactic_avg.set_xticks(np.arange(len(all_tactics)) + 0.5)
    ax_tactic_avg.set_xticklabels(all_tactics, fontsize=content_label_size)

    # For test case averages (left plot)
    ax_testcase_avg.tick_params(axis='y', which='both', labelleft=True)
    ax_testcase_avg.set_yticks(np.arange(len(all_test_cases)) + 0.5)
    ax_testcase_avg.set_yticklabels(all_test_cases, fontsize=content_label_size)
    
    # Adjust layout to prevent overlap
    plt.tight_layout(rect=[0, 0, 0.95, 0.95])  # Leave space for the title
    
    # Save the figure
    output_path = output_dir/output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved enhanced heatmap with averages to {output_filename}")
    

def calculate_success_stats(data):
    """Calculate success rate, confidence interval, and sample size for a group"""
    n = len(data)
    if n == 0:
        return 0, 0, 0
    
    success_rate = data.mean() * 100
    
    # Calculate 95% confidence interval using normal approximation
    if n > 1:
        se = np.sqrt((success_rate/100) * (1 - success_rate/100) / n)
        margin = 1.96 * se * 100
    else:
        margin = 0
        
    return success_rate, margin, n

def create_model_size_plot(df, output_dir, output_filename):
    """
    Create a plot showing success rate vs model size by turn type
    """
    # Add model size column
    df['model_size'] = df['target_model'].map(MODEL_SIZES)
    
    # Set GPT-4o-mini as a special case to be plotted separately
    df['is_gpt4o_mini'] = df['target_model'] == 'gpt-4o-mini-2024-07-18'
    
    # Process data for models
    results = []
    for turn_type in ['single', 'multi']:
        for model_size in sorted(df['model_size'].unique()):
            # Regular models (non-GPT4o-mini)
            subset = df[(df['turn_type'] == turn_type) & 
                        (df['model_size'] == model_size) & 
                        (~df['is_gpt4o_mini'])]
            
            if not subset.empty:
                success_rate, margin, n = calculate_success_stats(subset['goal_achieved'])
                results.append({
                    'turn_type': turn_type,
                    'model_size': model_size,
                    'is_gpt4o_mini': False,
                    'success_rate': success_rate,
                    'margin': margin,
                    'n': n
                })
            
            # GPT-4o-mini separately
            gpt4o_subset = df[(df['turn_type'] == turn_type) & 
                              (df['model_size'] == model_size) & 
                              (df['is_gpt4o_mini'])]
            
            if not gpt4o_subset.empty:
                success_rate, margin, n = calculate_success_stats(gpt4o_subset['goal_achieved'])
                results.append({
                    'turn_type': turn_type,
                    'model_size': model_size,
                    'is_gpt4o_mini': True,
                    'success_rate': success_rate,
                    'margin': margin,
                    'n': n
                })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Create the figure
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(111)
    
    # Set background color
    ax.set_facecolor('#f0f0f5')
    
    # Plot data points with error bars
    for turn_type, marker, color, linestyle in [
        ('single', 'o', 'blue', '-'),
        ('multi', 's', 'green', '--')
    ]:
        # Regular models
        regular_data = results_df[(results_df['turn_type'] == turn_type) & (~results_df['is_gpt4o_mini'])]
        
        if not regular_data.empty:
            regular_data = regular_data.sort_values('model_size')
            
            # Plot regular models with lines
            # TODO: Use asymmetric errorbar when succes_rate +/- margin is beyong 0 or 100
            ax.errorbar(
                regular_data['model_size'],
                regular_data['success_rate'],
                yerr=regular_data['margin'],
                fmt=marker,
                color=color,
                markersize=8,
                capsize=5,
                linestyle=linestyle,
                linewidth=2,
                label=f'{turn_type}-turn (n={regular_data["n"].sum()})'
            )
            
            # Add sample size annotations
            for _, row in regular_data.iterrows():
                ax.annotate(
                    f'n={row["n"]}',
                    xy=(row['model_size'], row['success_rate'] + 5),
                    ha='center',
                    va='top',
                    fontsize=8
                )
        
        # GPT-4o-mini as special point
        gpt4o_data = results_df[(results_df['turn_type'] == turn_type) & (results_df['is_gpt4o_mini'])]
        
        if not gpt4o_data.empty:
            marker_style = '^' if turn_type == 'single' else 'v'  # Triangle markers for GPT-4o-mini
            
            ax.errorbar(
                gpt4o_data['model_size'],
                gpt4o_data['success_rate'],
                yerr=gpt4o_data['margin'],
                fmt=marker_style,
                color='red',
                markersize=10,
                capsize=5,
                label=f'{turn_type}-turn GPT-4o-mini (n={gpt4o_data["n"].sum()})'
            )
            
            # Add sample size annotations
            for _, row in gpt4o_data.iterrows():
                ax.annotate(
                    f'n={row["n"]}',
                    xy=(row['model_size'], row['success_rate'] - 5),
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    color='red'
                )
    
    # Set x-axis to log scale
    ax.set_xscale('log')
    
    # Set limits and labels
    ax.set_ylim(0, 100)
    ax.set_xlim(0.8, 700)
    ax.set_xlabel('Model Size (B parameters)', fontsize=12)
    ax.set_ylabel('Success Rate (%)', fontsize=12)
    ax.set_title('Attack Success Rate vs Model Size by Turn Type', fontsize=14)
    
    # Format x-axis ticks
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.get_major_formatter().set_scientific(False)
    
    # Add legend
    ax.legend(loc='upper left', bbox_to_anchor=(1.01,1), fontsize=10)
    
    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Save and show
    plt.tight_layout()

    output_path = output_dir/output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved model size plot to {output_filename}")

def create_model_bar_plot(df, output_dir, output_filename='success_rate_by_model_name.png'):
    """
    Create a bar plot showing success rate by model name (ordered by model size) and turn type
    """
    # Add model size column
    df['model_size'] = df['target_model'].map(MODEL_SIZES)
    
    # Process data for models
    results = []
    for turn_type in ['single', 'multi']:
        for model_name in df['target_model'].unique():
            subset = df[(df['turn_type'] == turn_type) & (df['target_model'] == model_name)]
            
            if not subset.empty:
                success_rate, margin, n = calculate_success_stats(subset['goal_achieved'])
                model_size = MODEL_SIZES.get(model_name, 0)  # Get model size for ordering
                results.append({
                    'turn_type': turn_type,
                    'model_name': model_name,
                    'model_size': model_size,  # For ordering
                    'success_rate': success_rate,
                    'margin': margin,
                    'n': n
                })
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Create mapping of model names to display names (shorter for readability)
    display_names = {
        "gpt-4o-mini-2024-07-18": "GPT-4o-mini",
        "meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B",
        "meta-llama/llama-3.1-70b-instruct": "Llama 3.1 70B",
        "meta-llama/llama-3.1-405b-instruct": "Llama 3.1 405B",
        "meta-llama/llama-3.2-1b-instruct": "Llama 3.2 1B",
        "meta-llama/llama-3.2-3b-instruct": "Llama 3.2 3B",
        "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B"
    }
    
    # Add display name column
    results_df['display_name'] = results_df['model_name'].map(display_names)
    
    # Create the figure
    plt.figure(figsize=(14, 8))
    ax = plt.subplot(111)
    
    # Set background color
    ax.set_facecolor('#f0f0f5')
    
    # Get unique model names ordered by model size
    ordered_models = sorted(results_df['model_name'].unique(), key=lambda x: MODEL_SIZES.get(x, 0))
    ordered_display_names = [display_names.get(model, model) for model in ordered_models]
    
    # Set width of bars
    bar_width = 0.35
    
    # Set positions for bars
    indices = np.arange(len(ordered_models))
    
    # Create bar plots for each turn type
    for i, (turn_type, color) in enumerate([('single', 'blue'), ('multi', 'green')]):
        # Filter data for this turn type
        turn_data = results_df[results_df['turn_type'] == turn_type]
        
        # Create a dictionary for easy lookup
        model_to_data = {row['model_name']: row for _, row in turn_data.iterrows()}
        
        # Prepare data in the correct order
        success_rates = []
        error_bars = []
        sample_sizes = []
        
        for model in ordered_models:
            if model in model_to_data:
                row = model_to_data[model]
                success_rates.append(row['success_rate'])
                error_bars.append(row['margin'])
                sample_sizes.append(row['n'])
            else:
                success_rates.append(0)
                error_bars.append(0)
                sample_sizes.append(0)
        
        # Plot bars
        ax.bar(
            indices + (i * bar_width - bar_width/2),  # Position bars side by side
            success_rates,
            bar_width,
            color=color,
            alpha=0.7,
            label=f'{turn_type}-turn'
        )
        
        # Add error bars
        ax.errorbar(
            indices + (i * bar_width - bar_width/2),
            success_rates,
            yerr=error_bars,
            fmt='none',
            color='black',
            capsize=5
        )
        
        # # Add sample size annotations
        # for j, (rate, n) in enumerate(zip(success_rates, sample_sizes)):
        #     if n > 0:
        #         ax.annotate(
        #             f'n={n}',
        #             xy=(indices[j] + (i * bar_width - bar_width/2), rate + 3),
        #             ha='center',
        #             va='bottom',
        #             fontsize=8,
        #             color='black'
        #         )
    
    # Set x-axis labels
    ax.set_xticks(indices)
    ax.set_xticklabels(ordered_display_names, fontsize=20, rotation=45, ha='right')
    
    # Add model size underneath model names
    for i, model_name in enumerate(ordered_models):
        size = MODEL_SIZES.get(model_name, "Unknown")
        ax.annotate(
           f"{size}B params",
            xy=(i, -0.05),  # Position in data/axes coordinates
            xytext=(0, 0),  # No offset since we're using absolute position
            xycoords=('data', 'axes fraction'),
            textcoords='offset points',
            size=15,
            va='top',
            ha='center',
            rotation=45,
        )
    
    # Set limits and labels
    ax.set_ylim(0, 100)
    ax.set_xlabel('Model Name (Parameter Size)', fontsize=25)
    ax.set_ylabel('Success Rate (%)', fontsize=25)
    ax.tick_params(axis='y', labelsize=20)  # Set y-tick label size to 20
    # ax.set_title('Attack Success Rate by Model and Turn Type', fontsize=14)
    
    # Add legend
    ax.legend(loc='upper right', fontsize=20)
    
    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Save and show
    plt.subplots_adjust(bottom=0.25)
    
    output_path = output_dir/output_filename
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved model bar plot to {output_filename}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate plots from results data CSV file.')
    parser.add_argument('--csv', dest='csv_file', default='results.csv', help='Name of the CSV file under ../csv_results/ that will be used to generate plots (default: results.csv)')
    parser.add_argument('--version', dest='version', type=int, default=1, help='Version of the plot to generate (default: 1)')
    # Parse arguments
    args = parser.parse_args()
    root_dir = Path(__file__).resolve().parent.parent
    csv_file = root_dir/'csv_results'/args.csv_file
    
    # Extract filename without extension for use in output filenames
    csv_basename = os.path.splitext(os.path.basename(csv_file))[0]
    
    # Read the data
    print(f"Reading data from '{csv_file}'...")
    df = pd.read_csv(csv_file)
    
    print(f"Found {len(df)} rows of data")
    
    # Distinguish multi-turn data and single-turn data
    multi_turn_df = df[df['turn_type'] == 'multi']
    single_turn_df = df[df['turn_type'] == 'single']
    
    # Create output filenames with CSV basename suffix
    last_round_filename = f"last_round_score_heatmap_from_{csv_basename}.png"
    heatmap_filename = f"success_by_tactic_test_from_{csv_basename}.png"
    multi_heatmap_filename = f"success_by_tactic_test(multi)_from_{csv_basename}_v{args.version}.png"
    single_heatmap_filename = f"success_by_tactic_test(single)_from_{csv_basename}_v{args.version}.png"
    model_size_filename = f"success_rate_by_model_size_from_{csv_basename}.png"
    model_bar_filename = f"success_rate_by_model_name_from_{csv_basename}.png"

    plot_outputs_folder = root_dir/"plot_outputs"
    plot_outputs_folder.mkdir(exist_ok=True)
        
    # Create all plots
    print("Creating last round score heatmap...")
    create_last_round_split_cell_heatmap(df, plot_outputs_folder, last_round_filename)
    
    print("Creating success rate heatmap (both)...")
    create_refined_split_cell_heatmap(df, plot_outputs_folder, heatmap_filename)

    print("Creating success rate heatmap (multi)...")
    create_success_heatmap(multi_turn_df, plot_outputs_folder, multi_heatmap_filename, 'multi', version=args.version)
    
    print("Creating success rate heatmap (single)...")
    create_success_heatmap(single_turn_df, plot_outputs_folder, single_heatmap_filename, 'single', version=args.version)
    
    # plot_outputs_folder = root_dir/"plot_outputs"/"result_by_model"/csv_basename
    # plot_outputs_folder.mkdir(exist_ok=True, parents=True)
    # for key in MODEL_SIZES:
    #     create_last_round_split_cell_heatmap(df, plot_outputs_folder, last_round_filename, target_model=key)
    #     create_refined_split_cell_heatmap(df, plot_outputs_folder, heatmap_filename, target_model=key)
    #     create_success_heatmap(multi_turn_df, plot_outputs_folder, multi_heatmap_filename, 'multi', target_model=key)
    #     create_success_heatmap(multi_turn_df, plot_outputs_folder, multi_heatmap_filename, 'single', target_model=key)
        
    # plot_outputs_folder = root_dir/"plot_outputs"
    
    print("Creating model size line plot...")
    create_model_size_plot(df, plot_outputs_folder, model_size_filename)
    
    print("Creating model name bar plot...")
    create_model_bar_plot(df, plot_outputs_folder, model_bar_filename)
    
    print("Done!")

if __name__ == "__main__":
    main()
