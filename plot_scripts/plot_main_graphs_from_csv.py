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

def create_success_heatmap(df, output_dir, output_filename):
    """
    Create a heatmap showing success rate by jailbreak tactic and test case
    with average success rates for each tactic and test case
    """
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
    
    # Create the figure with extra space for averages
    plt.figure(figsize=(16, 12))
    
    # Define subplot layout to accommodate averages
    # Using 3 columns: [avg column, main heatmap, colorbar space]
    gs = plt.GridSpec(2, 3, width_ratios=[2, 20, 0.5], height_ratios=[20, 1], 
                     wspace=0.05, hspace=0.05)
    
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
                
                ax_main.text(j + 0.5, i + 0.5, text,
                        ha='center', va='center', color=text_color)
    
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
    
    ax_tactic_avg.set_xlabel('Jailbreak Tactic', fontsize=12)
    ax_tactic_avg.set_ylabel('', rotation=0)
    
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
    
    # Add empty plot for the bottom left square
    ax_empty = plt.subplot(gs[1, 0])
    ax_empty.axis('off')
    
    # Add colorbar to the main heatmap
    cbar_ax = plt.subplot(gs[0, 2])
    cbar = plt.colorbar(hm.get_children()[0], cax=cbar_ax)
    cbar.set_label('Success Rate (%)', fontsize=12)
    
    # Add title and labels for main plot
    plt.suptitle('Success Rate (%) by Tactic and Test Case', fontsize=16)
    ax_main.set_xlabel('')
    ax_main.set_ylabel('')  # Remove duplicate y-axis label
    
    # Set the y-axis label only on the averages plot since it's on the left now
    ax_testcase_avg.set_ylabel('Test Case', fontsize=12)
    
    # Rotate x-axis labels for better readability
    plt.setp(ax_main.get_xticklabels(), rotation=45, ha='right')
    
    # Fix the duplicate axis labels
    plt.setp(ax_testcase_avg.get_yticklabels(), visible=True)  # Keep left labels visible
    plt.setp(ax_main.get_yticklabels(), visible=False)  # Hide main heatmap y labels
    plt.setp(ax_tactic_avg.get_yticklabels(), visible=False)  # Hide bottom avg y labels
    
    # Fix the duplicate x-axis labels
    plt.setp(ax_tactic_avg.get_xticklabels(), visible=True)  # Keep bottom x labels visible
    plt.setp(ax_main.get_xticklabels(), visible=False)  # Hide main heatmap x labels
    
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
        
        # Add sample size annotations
        for j, (rate, n) in enumerate(zip(success_rates, sample_sizes)):
            if n > 0:
                ax.annotate(
                    f'n={n}',
                    xy=(indices[j] + (i * bar_width - bar_width/2), rate + 3),
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    color='black'
                )
    
    # Set x-axis labels
    ax.set_xticks(indices)
    ax.set_xticklabels(ordered_display_names, rotation=45, ha='right')
    
    # Add model size underneath model names
    for i, model_name in enumerate(ordered_models):
        size = MODEL_SIZES.get(model_name, "Unknown")
        ax.annotate(
           f"{size}B params",
            xy=(i, -0.05),  # Position in data/axes coordinates
            xytext=(0, 0),  # No offset since we're using absolute position
            xycoords=('data', 'axes fraction'),
            textcoords='offset points',
            size=8,
            va='top',
            ha='center',
            rotation=45
        )
    
    # Set limits and labels
    ax.set_ylim(0, 100)
    ax.set_xlabel('Model Name (Parameter Size)', fontsize=12)
    ax.set_ylabel('Success Rate (%)', fontsize=12)
    ax.set_title('Attack Success Rate by Model and Turn Type', fontsize=14)
    
    # Add legend
    ax.legend(loc='upper right', fontsize=10)
    
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
    
    # Create output filenames with CSV basename suffix
    heatmap_filename = f"success_by_tactic_test_from_{csv_basename}.png"
    model_size_filename = f"success_rate_by_model_size_from_{csv_basename}.png"
    model_bar_filename = f"success_rate_by_model_name_from_{csv_basename}.png"

    plot_outputs_folder = root_dir/"plot_outputs"
    plot_outputs_folder.mkdir(exist_ok=True)
        
    # Create all plots
    print("Creating success rate heatmap...")
    create_success_heatmap(df, plot_outputs_folder, heatmap_filename)
    
    print("Creating model size line plot...")
    create_model_size_plot(df, plot_outputs_folder, model_size_filename)
    
    print("Creating model name bar plot...")
    create_model_bar_plot(df, plot_outputs_folder, model_bar_filename)
    
    print("Done!")

if __name__ == "__main__":
    main()
