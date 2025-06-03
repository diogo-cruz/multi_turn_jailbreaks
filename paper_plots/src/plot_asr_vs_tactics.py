#!/usr/bin/env python3
"""
Bar plot of ASR vs tactics (averaged over models).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set up matplotlib to use LaTeX
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.size': 12
})

def calculate_asr_by_tactic(df, temp=0.0):
    """
    Calculate Attack Success Rate by tactic (average over test cases and models, temp 0)
    """
    # Filter for temperature 0
    df_temp = df[df['target_temp'] == temp].copy()
    
    # Group by tactic, turn_type, and model, then calculate ASR per model for each tactic
    asr_by_model = (df_temp.groupby(['jailbreak_tactic', 'turn_type', 'target_model'])['goal_achieved']
                    .mean().reset_index())
    
    # Average over models for each tactic and turn type
    asr_by_tactic = (asr_by_model.groupby(['jailbreak_tactic', 'turn_type'])['goal_achieved']
                     .mean().reset_index())
    
    return asr_by_tactic

def main():
    # Load data
    df = pd.read_csv('../../csv_results/master_results.csv')
    
    # Calculate ASR by tactic
    asr_data = calculate_asr_by_tactic(df)
    
    # Get unique tactics and sort them
    tactics = sorted(asr_data['jailbreak_tactic'].unique())
    
    # Prepare data for plotting
    multi_asr = []
    single_asr = []
    
    for tactic in tactics:
        tactic_data = asr_data[asr_data['jailbreak_tactic'] == tactic]
        
        multi_data = tactic_data[tactic_data['turn_type'] == 'multi']
        single_data = tactic_data[tactic_data['turn_type'] == 'single']
        
        multi_asr.append(multi_data['goal_achieved'].iloc[0] if not multi_data.empty else 0)
        single_asr.append(single_data['goal_achieved'].iloc[0] if not single_data.empty else 0)
    
    # Create the bar plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    x = np.arange(len(tactics))
    width = 0.35
    
    # Create bars
    bars1 = ax.bar(x - width/2, multi_asr, width, label='Multi-turn', alpha=0.8)
    bars2 = ax.bar(x + width/2, single_asr, width, label='Single-turn', alpha=0.8)
    
    # Customize plot
    ax.set_xlabel('Jailbreak Tactic')
    ax.set_ylabel('Attack Success Rate (ASR)')
    ax.set_title('Attack Success Rate by Jailbreak Tactic (Averaged over Models)')
    ax.set_xticks(x)
    
    # Format tactic names for better readability
    tactic_labels = []
    for tactic in tactics:
        # Replace underscores with spaces and capitalize
        formatted = tactic.replace('_', ' ').title()
        tactic_labels.append(formatted)
    
    ax.set_xticklabels(tactic_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max(max(multi_asr), max(single_asr)) * 1.1)
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=10)
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'asr_vs_tactics.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_tactics.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_dir / 'asr_vs_tactics.pdf'}")
    
    # Also create a horizontal bar plot for better readability
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    y = np.arange(len(tactics))
    height = 0.35
    
    # Create horizontal bars
    bars1 = ax.barh(y - height/2, multi_asr, height, label='Multi-turn', alpha=0.8)
    bars2 = ax.barh(y + height/2, single_asr, height, label='Single-turn', alpha=0.8)
    
    # Customize plot
    ax.set_ylabel('Jailbreak Tactic')
    ax.set_xlabel('Attack Success Rate (ASR)')
    ax.set_title('Attack Success Rate by Jailbreak Tactic (Averaged over Models)')
    ax.set_yticks(y)
    ax.set_yticklabels(tactic_labels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, max(max(multi_asr), max(single_asr)) * 1.1)
    
    # Add value labels on bars
    def add_value_labels_horizontal(bars):
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2.,
                   f'{width:.2f}', ha='left', va='center', fontsize=10)
    
    add_value_labels_horizontal(bars1)
    add_value_labels_horizontal(bars2)
    
    plt.tight_layout()
    
    plt.savefig(output_dir / 'asr_vs_tactics_horizontal.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_tactics_horizontal.png', dpi=300, bbox_inches='tight')
    print(f"Horizontal plot saved to {output_dir / 'asr_vs_tactics_horizontal.pdf'}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    for i, tactic in enumerate(tactics):
        print(f"{tactic_labels[i]:20} | Multi-turn: {multi_asr[i]:.3f} | Single-turn: {single_asr[i]:.3f}")
    
    plt.show()

if __name__ == '__main__':
    main() 