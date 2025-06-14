#!/usr/bin/env python3
"""
Single-turn vs Multi-turn ASR comparison using Cleveland dot plots.
Focuses on GPT-4o-mini as attacker/evaluator at temperature 0.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set up matplotlib 
plt.rcParams.update({
    'text.usetex': False,
    'font.family': 'serif',
    'font.size': 12
})

def filter_and_prepare_data(df):
    """
    Filter data according to specifications:
    - Temperature 0
    - GPT-4o-mini as attacker and evaluator
    - Ignore data where reasoning is filled but not none
    """
    # Filter for temperature 0
    df_filtered = df[df['target_temp'] == 0.0].copy()
    
    # Filter for GPT-4o-mini as both attacker and evaluator
    df_filtered = df_filtered[
        (df_filtered['attacker_model'] == 'openai/gpt-4o-mini-2024-07-18') &
        (df_filtered['evaluator_model'] == 'openai/gpt-4o-mini')
    ].copy()
    
    # Filter out data where reasoning is filled but not 'none'
    # (Keep data where reasoning is 'none' or NaN/empty)
    df_filtered = df_filtered[
        (df_filtered['reasoning'].isna()) |
        (df_filtered['reasoning'] == 'none') |
        (df_filtered['reasoning'] == '')
    ].copy()
    
    print(f"After filtering: {len(df_filtered)} records remaining")
    return df_filtered

def calculate_asr_by_model(df):
    """
    Calculate ASR by target model and turn type
    """
    # Group by model and turn type, calculate mean ASR
    asr_data = (df.groupby(['target_model', 'turn_type'])['goal_achieved']
                .agg(['mean', 'count']).reset_index())
    asr_data.columns = ['target_model', 'turn_type', 'asr', 'count']
    
    # Pivot to have single and multi columns
    asr_pivot = asr_data.pivot(index='target_model', columns='turn_type', values='asr').fillna(0)
    count_pivot = asr_data.pivot(index='target_model', columns='turn_type', values='count').fillna(0)
    
    # Combine into final dataframe
    result = pd.DataFrame({
        'model': asr_pivot.index,
        'single_asr': asr_pivot.get('single', 0),
        'multi_asr': asr_pivot.get('multi', 0),
        'single_count': count_pivot.get('single', 0),
        'multi_count': count_pivot.get('multi', 0)
    })
    
    # Filter models with sufficient data (at least 5 samples in each)
    result = result[
        (result['single_count'] >= 5) & 
        (result['multi_count'] >= 5)
    ].copy()
    
    # Calculate difference for sorting
    result['diff'] = result['multi_asr'] - result['single_asr']
    
    # Sort by multi-turn ASR for better visualization
    result = result.sort_values('multi_asr', ascending=True)
    
    return result

def create_cleveland_dot_plot(asr_data):
    """
    Create Cleveland dot plot for single-turn vs multi-turn ASR
    """
    fig, ax = plt.subplots(figsize=(10, max(8, len(asr_data) * 0.4)))
    
    # Get top models for better readability
    top_models = asr_data.head(10) if len(asr_data) > 10 else asr_data
    
    y_pos = np.arange(len(top_models))
    
    # Plot lines connecting single and multi-turn points
    for i, (_, row) in enumerate(top_models.iterrows()):
        ax.plot([row['single_asr'], row['multi_asr']], [i, i], 
                'k-', alpha=0.3, linewidth=1)
    
    # Plot points
    ax.scatter(top_models['single_asr'], y_pos, 
               color='blue', s=60, alpha=0.7, label='Single-turn', marker='o')
    ax.scatter(top_models['multi_asr'], y_pos, 
               color='red', s=60, alpha=0.7, label='Multi-turn', marker='s')
    
    # Customize plot
    ax.set_yticks(y_pos)
    model_labels = [model.split('/')[-1] if '/' in model else model 
                   for model in top_models['model']]
    ax.set_yticklabels(model_labels, fontsize=10)
    ax.set_xlabel('Attack Success Rate (ASR)')  
    ax.set_title('Single-turn vs Multi-turn ASR by Model\n(GPT-4o-mini attacker/evaluator, temp=0)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, 1.05)
    
    # Add difference annotations for largest differences
    for i, (_, row) in enumerate(top_models.iterrows()):
        diff = row['diff']
        if abs(diff) > 0.1:  # Only annotate significant differences
            mid_x = (row['single_asr'] + row['multi_asr']) / 2
            ax.annotate(f'{diff:+.2f}', xy=(mid_x, i), 
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    return fig

def create_bar_chart_alternative(asr_data):
    """
    Create alternative bar chart visualization
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get top models
    top_models = asr_data.head(10) if len(asr_data) > 10 else asr_data
    
    x = np.arange(len(top_models))
    width = 0.35
    
    # Create bars
    bars1 = ax.bar(x - width/2, top_models['single_asr'], width, 
                   label='Single-turn', alpha=0.8, color='blue')
    bars2 = ax.bar(x + width/2, top_models['multi_asr'], width, 
                   label='Multi-turn', alpha=0.8, color='red')
    
    # Customize plot
    ax.set_xlabel('Target Model')
    ax.set_ylabel('Attack Success Rate (ASR)')
    ax.set_title('Single-turn vs Multi-turn ASR by Model\n(GPT-4o-mini attacker/evaluator, temp=0)')
    ax.set_xticks(x)
    
    model_labels = [model.split('/')[-1] if '/' in model else model 
                   for model in top_models['model']]
    ax.set_xticklabels(model_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.05)
    
    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0.01:  # Only label non-zero bars
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=8)
    
    add_value_labels(bars1)
    add_value_labels(bars2)
    
    plt.tight_layout()
    return fig

def main():
    # Load data
    print("Loading data...")
    df = pd.read_csv('../../csv_results/master_results.csv')
    print(f"Total records: {len(df)}")
    
    # Filter and prepare data
    df_filtered = filter_and_prepare_data(df)
    
    if len(df_filtered) == 0:
        print("No data remaining after filtering!")
        return
    
    # Calculate ASR by model
    asr_data = calculate_asr_by_model(df_filtered)
    print(f"Models with sufficient data: {len(asr_data)}")
    
    if len(asr_data) == 0:
        print("No models with sufficient data!")
        return
    
    # Create output directory
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    
    # Create Cleveland dot plot (preferred)
    print("Creating Cleveland dot plot...")
    fig1 = create_cleveland_dot_plot(asr_data)
    fig1.savefig(output_dir / 'single_vs_multi_turn_cleveland.pdf', dpi=300, bbox_inches='tight')
    fig1.savefig(output_dir / 'single_vs_multi_turn_cleveland.png', dpi=300, bbox_inches='tight')
    print(f"Cleveland dot plot saved to {output_dir / 'single_vs_multi_turn_cleveland.pdf'}")
    
    # Create bar chart alternative
    print("Creating bar chart alternative...")
    fig2 = create_bar_chart_alternative(asr_data)
    fig2.savefig(output_dir / 'single_vs_multi_turn_bars.pdf', dpi=300, bbox_inches='tight')
    fig2.savefig(output_dir / 'single_vs_multi_turn_bars.png', dpi=300, bbox_inches='tight')
    print(f"Bar chart saved to {output_dir / 'single_vs_multi_turn_bars.pdf'}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    print(f"{'Model':<40} {'Single':<8} {'Multi':<8} {'Diff':<8} {'Samples'}")
    print("-" * 80)
    for _, row in asr_data.head(15).iterrows():
        model_short = row['model'].split('/')[-1] if '/' in row['model'] else row['model']
        model_short = model_short[:35] + "..." if len(model_short) > 35 else model_short
        print(f"{model_short:<40} {row['single_asr']:.3f}    {row['multi_asr']:.3f}    {row['diff']:+.3f}    {int(row['single_count'])}/{int(row['multi_count'])}")
    
    # Overall statistics
    print(f"\nOverall Statistics:")
    print(f"Average Single-turn ASR: {asr_data['single_asr'].mean():.3f}")
    print(f"Average Multi-turn ASR: {asr_data['multi_asr'].mean():.3f}")
    print(f"Average Difference (Multi - Single): {asr_data['diff'].mean():.3f}")
    print(f"Models where Multi > Single: {len(asr_data[asr_data['diff'] > 0])}/{len(asr_data)}")
    
    plt.show()

if __name__ == '__main__':
    main() 