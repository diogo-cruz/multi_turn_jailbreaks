#!/usr/bin/env python3
"""
Plot ASR vs model size for multi-turn (solid line) and single-turn (dashed line) settings.
Different model families should use different colors, and be labeled in the legend.
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

def calculate_asr(df, temp=0.0):
    """
    Calculate Attack Success Rate (maximum over tactics, average over test cases, temp 0)
    """
    # Filter for temperature 0
    df_temp = df[df['target_temp'] == temp].copy()
    
    # Group by model, turn_type, and tactic, then calculate ASR per tactic
    asr_by_tactic = (df_temp.groupby(['target_model', 'turn_type', 'jailbreak_tactic'])['goal_achieved']
                     .mean().reset_index())
    
    # Take maximum ASR over tactics for each model and turn type
    max_asr = (asr_by_tactic.groupby(['target_model', 'turn_type'])['goal_achieved']
               .max().reset_index())
    
    return max_asr

def main():
    # Import utilities
    from model_utils import get_model_data_with_info
    
    # Load data
    df = pd.read_csv('../../csv_results/master_results.csv')
    model_info = pd.read_csv('../../model_comparison.csv')
    
    # Calculate ASR
    asr_data = calculate_asr(df)
    
    # Merge with model information
    asr_with_info = get_model_data_with_info(asr_data, model_info, ['Parameters'])
    
    asr_df = pd.DataFrame(asr_with_info)
    
    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Get unique families and assign colors
    families = sorted(asr_df['family'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(families)))
    family_colors = dict(zip(families, colors))
    
    # Plot for each family
    for family in families:
        family_data = asr_df[asr_df['family'] == family]
        
        # Multi-turn (solid line)
        multi_data = family_data[family_data['turn_type'] == 'multi']
        if not multi_data.empty:
            multi_sorted = multi_data.sort_values('parameters')
            ax.plot(multi_sorted['parameters'], multi_sorted['asr'], 
                   color=family_colors[family], linestyle='-', marker='o',
                   label=f'{family} (Multi-turn)', linewidth=2, markersize=6)
        
        # Single-turn (dashed line)
        single_data = family_data[family_data['turn_type'] == 'single']
        if not single_data.empty:
            single_sorted = single_data.sort_values('parameters')
            ax.plot(single_sorted['parameters'], single_sorted['asr'], 
                   color=family_colors[family], linestyle='--', marker='s',
                   label=f'{family} (Single-turn)', linewidth=2, markersize=6)
    
    # Customize plot
    ax.set_xlabel('Model Size (Parameters in Billions)')
    ax.set_ylabel('Attack Success Rate (ASR)')
    ax.set_title('Attack Success Rate vs Model Size')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    
    # Use log scale for x-axis if range is large and we have data
    if not asr_df.empty:
        param_range = asr_df['parameters'].max() / asr_df['parameters'].min()
        if param_range > 10:
            ax.set_xscale('log')
            ax.set_xlabel('Model Size (Parameters in Billions, log scale)')
    else:
        print("Warning: No data available for model size plot")
        print("Check human_TODO.md for missing model information")
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'asr_vs_model_size.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_model_size.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_dir / 'asr_vs_model_size.pdf'}")
    
    plt.show()

if __name__ == '__main__':
    main() 