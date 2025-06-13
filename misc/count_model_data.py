#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Count the number of data points per model in master_results.csv
This will show how many entries exist for each model, broken down by turn type.
"""

import pandas as pd
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def count_model_data(csv_file):
    """
    Count the number of data points for each model in the CSV file.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        dict: Dictionary with counts for each model
    """
    print(f"Reading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"Found {len(df)} total rows of data")
    
    # Get unique models
    models = sorted(df['target_model'].unique())
    print(f"Found {len(models)} unique models")
    
    # Count data points by model and turn type
    results = defaultdict(lambda: {'multi': 0, 'single': 0, 'total': 0})
    
    for model in models:
        model_df = df[df['target_model'] == model]
        multi_count = len(model_df[model_df['turn_type'] == 'multi'])
        single_count = len(model_df[model_df['turn_type'] == 'single'])
        total_count = len(model_df)
        
        results[model] = {
            'multi': multi_count,
            'single': single_count,
            'total': total_count
        }
    
    return results

def print_model_counts(counts):
    """
    Print the model counts in a formatted table.
    
    Args:
        counts: Dictionary with counts for each model
    """
    print("\nModel Data Counts:")
    print("-" * 80)
    print(f"{'Model':<40} | {'Multi-Turn':>12} | {'Single-Turn':>12} | {'Total':>12}")
    print("-" * 80)
    
    # Calculate totals
    multi_total = sum(data['multi'] for data in counts.values())
    single_total = sum(data['single'] for data in counts.values())
    grand_total = sum(data['total'] for data in counts.values())
    
    # Print each model's counts
    for model, data in counts.items():
        print(f"{model:<40} | {data['multi']:>12,} | {data['single']:>12,} | {data['total']:>12,}")
    
    # Print totals
    print("-" * 80)
    print(f"{'TOTAL':<40} | {multi_total:>12,} | {single_total:>12,} | {grand_total:>12,}")
    print("-" * 80)

def save_counts_to_csv(counts, output_file):
    """
    Save the counts to a CSV file.
    
    Args:
        counts: Dictionary with counts for each model
        output_file: Path to the output CSV file
    """
    # Create a DataFrame from the counts
    data = []
    for model, count_data in counts.items():
        data.append({
            'model': model,
            'multi_turn': count_data['multi'],
            'single_turn': count_data['single'],
            'total': count_data['total']
        })
    
    df = pd.DataFrame(data)
    
    # Sort by total count (descending)
    df = df.sort_values('total', ascending=False)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Saved counts to {output_file}")

def plot_model_counts(counts, output_file):
    """
    Create a horizontal bar chart of model counts.
    
    Args:
        counts: Dictionary with counts for each model
        output_file: Path to the output image file
    """
    # Create a DataFrame from the counts
    data = []
    for model, count_data in counts.items():
        # Get short model name (last part after '/')
        short_name = model.split('/')[-1]
        data.append({
            'model': short_name,
            'multi_turn': count_data['multi'],
            'single_turn': count_data['single'],
            'total': count_data['total']
        })
    
    df = pd.DataFrame(data)
    
    # Sort by total count (descending)
    df = df.sort_values('total', ascending=False)
    
    # Set up the plot
    plt.figure(figsize=(12, max(8, len(df) * 0.3)))  # Adjust height based on number of models
    
    # Create the bar positions
    y_pos = range(len(df))
    
    # Plot the bars
    plt.barh(y_pos, df['multi_turn'], color='green', label='Multi-Turn')
    plt.barh(y_pos, df['single_turn'], color='blue', left=df['multi_turn'], label='Single-Turn')
    
    # Set the labels and title
    plt.yticks(y_pos, df['model'])
    plt.xlabel('Number of Data Points')
    plt.title('Number of Data Points per Model')
    
    # Add a grid
    plt.grid(axis='x', alpha=0.3)
    
    # Add a legend
    plt.legend()
    
    # Add annotations with count values
    for i, (_, row) in enumerate(df.iterrows()):
        multi_pos = row['multi_turn'] / 2  # Position for multi-turn label
        single_pos = row['multi_turn'] + (row['single_turn'] / 2)  # Position for single-turn label
        
        plt.text(multi_pos, i, str(row['multi_turn']), 
                 ha='center', va='center', color='white' if row['multi_turn'] > 100 else 'black')
        
        plt.text(single_pos, i, str(row['single_turn']), 
                 ha='center', va='center', color='white' if row['single_turn'] > 100 else 'black')
        
        # Add total on the right
        plt.text(row['total'] + 10, i, f"Total: {row['total']}", 
                 ha='left', va='center', color='black')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {output_file}")

def analyze_test_cases_and_tactics(csv_file):
    """
    Analyze the distribution of test cases and tactics in the dataset.
    
    Args:
        csv_file: Path to the CSV file
    """
    df = pd.read_csv(csv_file)
    
    # Count unique test cases and tactics
    test_cases = df['test_case'].unique()
    tactics = df['jailbreak_tactic'].unique()
    
    print(f"\nFound {len(test_cases)} unique test cases and {len(tactics)} unique jailbreak tactics")
    
    # Print list of test cases
    print("\nTest Cases:")
    for test_case in sorted(test_cases):
        print(f"- {test_case}")
    
    # Print list of tactics
    print("\nJailbreak Tactics:")
    for tactic in sorted(tactics):
        print(f"- {tactic}")

def main():
    # Path to the CSV file
    csv_file = os.path.join('csv_results', 'master_results.csv')
    
    # Check if the file exists
    if not os.path.exists(csv_file):
        print(f"Error: CSV file {csv_file} not found")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs('model_analysis', exist_ok=True)
    
    # Output files
    csv_output = os.path.join('model_analysis', 'model_counts.csv')
    plot_output = os.path.join('model_analysis', 'model_counts.png')
    
    # Count the data points for each model
    counts = count_model_data(csv_file)
    
    # Print the results
    print_model_counts(counts)
    
    # Save to CSV
    save_counts_to_csv(counts, csv_output)
    
    # Create visualization
    plot_model_counts(counts, plot_output)
    
    # Analyze test cases and tactics
    analyze_test_cases_and_tactics(csv_file)

if __name__ == "__main__":
    main() 