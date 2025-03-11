#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter
#import scipy.stats as stats

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

def create_success_heatmap(df, output_filename='success_by_tactic_test.png'):
    """
    Create a heatmap showing success rate by jailbreak tactic and test case
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
        aggfunc=lambda x: x.std(ddof=1) if len(x) > 1 else 0 # use ddof=1 to get the sample std
    ) * 100
    
    # Calculate sample sizes
    sample_sizes = df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='count'
    )
    
    # Create the figure
    plt.figure(figsize=(14, 10))
    
    # Create heatmap with mean values
    ax = sns.heatmap(success_means, annot=False, fmt='.1f', cmap='YlOrRd', vmin=0, vmax=100)
    
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
                
                plt.text(j + 0.5, i + 0.5, text,
                        ha='center', va='center', color=text_color)
    
    # Add title and labels
    plt.title('Success Rate (%) by Tactic and Test Case', fontsize=16)
    plt.xlabel('Jailbreak Tactic', fontsize=12)
    plt.ylabel('Test Case', fontsize=12)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add a colorbar label
    cbar = ax.collections[0].colorbar
    cbar.set_label('Success Rate (%)', fontsize=12)
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved heatmap to {output_filename}")

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

def create_model_size_plot(df, output_filename='success_rate_by_model_size.png'):
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
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved model size plot to {output_filename}")

def create_model_bar_plot(df, output_filename='success_rate_by_model_name.png'):
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
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved model bar plot to {output_filename}")

def main():
    # Read the data
    print("Reading data from 'results_data.csv'...")
    df = pd.read_csv('yolanda_clean_results_data.csv')
    
    print(f"Found {len(df)} rows of data")
    
    # Create both plots
    print("Creating success rate heatmap...")
    create_success_heatmap(df)
    
    print("Creating model size line plot...")
    create_model_size_plot(df)
    
    print("Creating model name bar plot...")
    create_model_bar_plot(df)
    
    print("Done!")

if __name__ == "__main__":
    main()
