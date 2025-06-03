#!/usr/bin/env python3
"""
Plot ASR vs reasoning effort (using only data where reasoning is specified).
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

def extract_model_family(model_name):
    """Extract model family from model name"""
    if 'deepseek' in model_name.lower():
        return 'DeepSeek'
    elif 'claude' in model_name.lower() or 'anthropic' in model_name.lower():
        return 'Anthropic'
    elif 'gemini' in model_name.lower() or 'gemma' in model_name.lower():
        return 'Google'
    elif 'llama' in model_name.lower() or 'meta' in model_name.lower():
        return 'Meta'
    elif 'mistral' in model_name.lower():
        return 'Mistral'
    elif 'qwen' in model_name.lower():
        return 'Qwen'
    elif 'gpt' in model_name.lower() or 'openai' in model_name.lower():
        return 'OpenAI'
    elif 'grok' in model_name.lower() or 'x-ai' in model_name.lower():
        return 'xAI'
    else:
        return 'Other'

def calculate_asr_by_reasoning(df, temp=0.0):
    """
    Calculate Attack Success Rate by reasoning level (maximum over tactics, average over test cases, temp 0)
    """
    # Filter for temperature 0 and non-null reasoning
    df_temp = df[(df['target_temp'] == temp) & (df['reasoning'].notna()) & (df['reasoning'] != 'none')].copy()
    
    # Group by model, turn_type, reasoning, and tactic, then calculate ASR per tactic
    asr_by_tactic = (df_temp.groupby(['target_model', 'turn_type', 'reasoning', 'jailbreak_tactic'])['goal_achieved']
                     .mean().reset_index())
    
    # Take maximum ASR over tactics for each model, turn type, and reasoning level
    max_asr = (asr_by_tactic.groupby(['target_model', 'turn_type', 'reasoning'])['goal_achieved']
               .max().reset_index())
    
    return max_asr

def main():
    # Import utilities
    from model_utils import extract_model_family
    
    # Load data
    df = pd.read_csv('../../csv_results/master_results.csv')
    
    # Calculate ASR by reasoning level
    asr_data = calculate_asr_by_reasoning(df)
    
    # Check if we have enough data
    if asr_data.empty:
        print("No reasoning data available for plotting!")
        print("Note: Only 4.5% of experimental data has reasoning level information.")
        print("See human_TODO.md for recommendations on filling reasoning data.")
        return
    
    print(f"Found {len(asr_data)} data points with reasoning information")
    print("Note: This represents only models/test cases with explicit reasoning levels")
    
    # Add model family information
    asr_data['family'] = asr_data['target_model'].apply(extract_model_family)
    
    # Define reasoning level order
    reasoning_order = ['low', 'medium', 'high']
    asr_data = asr_data[asr_data['reasoning'].isin(reasoning_order)]
    
    # Create categorical variable for proper ordering
    asr_data['reasoning_cat'] = pd.Categorical(asr_data['reasoning'], categories=reasoning_order, ordered=True)
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Get unique families and assign colors
    families = sorted(asr_data['family'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(families)))
    family_colors = dict(zip(families, colors))
    
    # Plot 1: Multi-turn
    multi_data = asr_data[asr_data['turn_type'] == 'multi']
    for family in families:
        family_data = multi_data[multi_data['family'] == family]
        if not family_data.empty:
            # Calculate mean ASR per reasoning level for this family
            family_asr = family_data.groupby('reasoning_cat')['goal_achieved'].mean()
            ax1.plot(range(len(reasoning_order)), 
                    [family_asr.get(level, 0) for level in reasoning_order],
                    color=family_colors[family], marker='o', linewidth=2, markersize=8,
                    label=family)
    
    ax1.set_xlabel('Reasoning Level')
    ax1.set_ylabel('Attack Success Rate (ASR)')
    ax1.set_title('Multi-turn ASR vs Reasoning Level')
    ax1.set_xticks(range(len(reasoning_order)))
    ax1.set_xticklabels([r.capitalize() for r in reasoning_order])
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(0, 1)
    
    # Plot 2: Single-turn
    single_data = asr_data[asr_data['turn_type'] == 'single']
    for family in families:
        family_data = single_data[single_data['family'] == family]
        if not family_data.empty:
            # Calculate mean ASR per reasoning level for this family
            family_asr = family_data.groupby('reasoning_cat')['goal_achieved'].mean()
            ax2.plot(range(len(reasoning_order)), 
                    [family_asr.get(level, 0) for level in reasoning_order],
                    color=family_colors[family], marker='s', linewidth=2, markersize=8,
                    label=family)
    
    ax2.set_xlabel('Reasoning Level')
    ax2.set_ylabel('Attack Success Rate (ASR)')
    ax2.set_title('Single-turn ASR vs Reasoning Level')
    ax2.set_xticks(range(len(reasoning_order)))
    ax2.set_xticklabels([r.capitalize() for r in reasoning_order])
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'asr_vs_reasoning.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_reasoning.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_dir / 'asr_vs_reasoning.pdf'}")
    
    # Also create a combined plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Combined plot with both turn types
    for family in families:
        # Multi-turn data
        family_multi = multi_data[multi_data['family'] == family]
        if not family_multi.empty:
            family_asr = family_multi.groupby('reasoning_cat')['goal_achieved'].mean()
            x_pos = np.array(range(len(reasoning_order))) - 0.1
            ax.plot(x_pos, [family_asr.get(level, 0) for level in reasoning_order],
                   color=family_colors[family], marker='o', linewidth=2, markersize=8,
                   linestyle='-', label=f'{family} (Multi-turn)')
        
        # Single-turn data
        family_single = single_data[single_data['family'] == family]
        if not family_single.empty:
            family_asr = family_single.groupby('reasoning_cat')['goal_achieved'].mean()
            x_pos = np.array(range(len(reasoning_order))) + 0.1
            ax.plot(x_pos, [family_asr.get(level, 0) for level in reasoning_order],
                   color=family_colors[family], marker='s', linewidth=2, markersize=8,
                   linestyle='--', label=f'{family} (Single-turn)')
    
    ax.set_xlabel('Reasoning Level')
    ax.set_ylabel('Attack Success Rate (ASR)')
    ax.set_title('Attack Success Rate vs Reasoning Level')
    ax.set_xticks(range(len(reasoning_order)))
    ax.set_xticklabels([r.capitalize() for r in reasoning_order])
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'asr_vs_reasoning_combined.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_reasoning_combined.png', dpi=300, bbox_inches='tight')
    print(f"Combined plot saved to {output_dir / 'asr_vs_reasoning_combined.pdf'}")
    
    plt.show()

if __name__ == '__main__':
    main() 