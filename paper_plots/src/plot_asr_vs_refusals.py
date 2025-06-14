#!/usr/bin/env python3
"""
ASR vs Number of Refusals analysis.
Shows how ASR changes based on how many refusals we allow before considering an attack unsuccessful.
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
    df_filtered = df_filtered[
        (df_filtered['reasoning'].isna()) |
        (df_filtered['reasoning'] == 'none') |
        (df_filtered['reasoning'] == '')
    ].copy()
    
    print(f"After filtering: {len(df_filtered)} records remaining")
    return df_filtered

def calculate_asr_vs_refusals(df, max_refusals=10, approach='average'):
    """
    Calculate ASR vs number of refusals allowed.
    
    Args:
        df: Filtered dataframe
        max_refusals: Maximum number of refusals to consider
        approach: 'average' or 'max_over_tactics'
    """
    results = []
    
    for k in range(max_refusals + 1):
        if approach == 'average':
            # Average over samples, test cases, and tactics
            # For each data point, consider it successful if goal_achieved=True AND refused <= k
            df_k = df[df['refused'] <= k].copy()
            asr_by_combo = df_k.groupby(['target_model', 'turn_type', 'jailbreak_tactic', 'test_case'])['goal_achieved'].mean().reset_index()
            
            # Average over all dimensions
            asr_overall = asr_by_combo.groupby(['target_model', 'turn_type'])['goal_achieved'].mean().reset_index()
            
        elif approach == 'max_over_tactics':
            # For each (model, turn_type, test_case), take max over tactics
            df_k = df[df['refused'] <= k].copy()
            asr_by_combo = df_k.groupby(['target_model', 'turn_type', 'test_case', 'jailbreak_tactic'])['goal_achieved'].mean().reset_index()
            
            # Max over tactics for each (model, turn_type, test_case)
            asr_max_tactics = asr_by_combo.groupby(['target_model', 'turn_type', 'test_case'])['goal_achieved'].max().reset_index()
            
            # Average over test cases
            asr_overall = asr_max_tactics.groupby(['target_model', 'turn_type'])['goal_achieved'].mean().reset_index()
        
        # Calculate overall statistics
        for turn_type in ['single', 'multi']:
            turn_data = asr_overall[asr_overall['turn_type'] == turn_type]
            if not turn_data.empty:
                results.append({
                    'refusals_allowed': k,
                    'turn_type': turn_type,
                    'asr_mean': turn_data['goal_achieved'].mean(),
                    'asr_std': turn_data['goal_achieved'].std(),
                    'n_models': len(turn_data)
                })
    
    return pd.DataFrame(results)

def calculate_asr_by_tactic_and_refusals(df, max_refusals=10):
    """
    Calculate ASR vs refusals for each tactic separately
    """
    results = []
    
    for tactic in df['jailbreak_tactic'].unique():
        df_tactic = df[df['jailbreak_tactic'] == tactic].copy()
        
        for k in range(max_refusals + 1):
            df_k = df_tactic[df_tactic['refused'] <= k].copy()
            
            if len(df_k) > 0:
                # Calculate ASR for this tactic and refusal level
                asr_by_model = df_k.groupby(['target_model', 'turn_type'])['goal_achieved'].mean().reset_index()
                
                for turn_type in ['single', 'multi']:
                    turn_data = asr_by_model[asr_by_model['turn_type'] == turn_type]
                    if not turn_data.empty:
                        results.append({
                            'refusals_allowed': k,
                            'turn_type': turn_type,
                            'tactic': tactic,
                            'asr_mean': turn_data['goal_achieved'].mean(),
                            'asr_std': turn_data['goal_achieved'].std(),
                            'n_models': len(turn_data)
                        })
    
    return pd.DataFrame(results)

def create_asr_vs_refusals_plot(results_avg, results_max, max_refusals):
    """
    Create ASR vs refusals plot comparing average and max approaches
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Average approach
    for turn_type in ['single', 'multi']:
        data = results_avg[results_avg['turn_type'] == turn_type]
        color = 'blue' if turn_type == 'single' else 'red'
        ax1.plot(data['refusals_allowed'], data['asr_mean'], 
                'o-', color=color, label=f'{turn_type.title()}-turn', linewidth=2, markersize=6)
        
        # Add error bars
        ax1.fill_between(data['refusals_allowed'], 
                        data['asr_mean'] - data['asr_std'], 
                        data['asr_mean'] + data['asr_std'], 
                        alpha=0.2, color=color)
    
    ax1.set_xlabel('Maximum Refusals Allowed')
    ax1.set_ylabel('Attack Success Rate (ASR)')
    ax1.set_title('ASR vs Refusals\n(Average over tactics)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, max_refusals)
    ax1.set_ylim(0, 1)
    
    # Plot 2: Max over tactics approach
    for turn_type in ['single', 'multi']:
        data = results_max[results_max['turn_type'] == turn_type]
        color = 'blue' if turn_type == 'single' else 'red'
        ax2.plot(data['refusals_allowed'], data['asr_mean'], 
                'o-', color=color, label=f'{turn_type.title()}-turn', linewidth=2, markersize=6)
        
        # Add error bars
        ax2.fill_between(data['refusals_allowed'], 
                        data['asr_mean'] - data['asr_std'], 
                        data['asr_mean'] + data['asr_std'], 
                        alpha=0.2, color=color)
    
    ax2.set_xlabel('Maximum Refusals Allowed')
    ax2.set_ylabel('Attack Success Rate (ASR)')
    ax2.set_title('ASR vs Refusals\n(Max over tactics)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, max_refusals)
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    return fig

def create_tactic_specific_plot(results_by_tactic, max_refusals):
    """
    Create ASR vs refusals plot for different tactics
    """
    tactics = results_by_tactic['tactic'].unique()
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(tactics)))
    
    for turn_idx, turn_type in enumerate(['single', 'multi']):
        ax = axes[turn_idx]
        
        for tactic, color in zip(tactics, colors):
            data = results_by_tactic[
                (results_by_tactic['tactic'] == tactic) & 
                (results_by_tactic['turn_type'] == turn_type)
            ]
            
            if not data.empty:
                ax.plot(data['refusals_allowed'], data['asr_mean'], 
                       'o-', color=color, label=tactic.replace('_', ' ').title(), 
                       linewidth=2, markersize=4)
        
        ax.set_xlabel('Maximum Refusals Allowed')
        ax.set_ylabel('Attack Success Rate (ASR)')
        ax.set_title(f'{turn_type.title()}-turn: ASR vs Refusals by Tactic')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max_refusals)
        ax.set_ylim(0, 1)
    
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
    
    print(f"Refusal distribution:")
    print(df_filtered['refused'].value_counts().sort_index())
    
    max_refusals = min(10, df_filtered['refused'].max())
    print(f"Using max_refusals = {max_refusals}")
    
    # Calculate ASR vs refusals with different approaches
    print("Calculating ASR vs refusals (average approach)...")
    results_avg = calculate_asr_vs_refusals(df_filtered, max_refusals, 'average')
    
    print("Calculating ASR vs refusals (max over tactics approach)...")
    results_max = calculate_asr_vs_refusals(df_filtered, max_refusals, 'max_over_tactics')
    
    print("Calculating ASR vs refusals by tactic...")
    results_by_tactic = calculate_asr_by_tactic_and_refusals(df_filtered, max_refusals)
    
    # Create output directory
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    
    # Create main ASR vs refusals plot
    print("Creating main ASR vs refusals plot...")
    fig1 = create_asr_vs_refusals_plot(results_avg, results_max, max_refusals)
    fig1.savefig(output_dir / 'asr_vs_refusals_main.pdf', dpi=300, bbox_inches='tight')
    fig1.savefig(output_dir / 'asr_vs_refusals_main.png', dpi=300, bbox_inches='tight')
    print(f"Main plot saved to {output_dir / 'asr_vs_refusals_main.pdf'}")
    
    # Create tactic-specific plot
    print("Creating tactic-specific plot...")
    fig2 = create_tactic_specific_plot(results_by_tactic, max_refusals)
    fig2.savefig(output_dir / 'asr_vs_refusals_by_tactic.pdf', dpi=300, bbox_inches='tight')
    fig2.savefig(output_dir / 'asr_vs_refusals_by_tactic.png', dpi=300, bbox_inches='tight')
    print(f"Tactic-specific plot saved to {output_dir / 'asr_vs_refusals_by_tactic.pdf'}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    print("Average Approach:")
    for turn_type in ['single', 'multi']:
        data = results_avg[results_avg['turn_type'] == turn_type]
        print(f"{turn_type.title()}-turn:")
        for _, row in data.iterrows():
            print(f"  {row['refusals_allowed']} refusals: ASR = {row['asr_mean']:.3f} ± {row['asr_std']:.3f}")
    
    print("\nMax over Tactics Approach:")
    for turn_type in ['single', 'multi']:
        data = results_max[results_max['turn_type'] == turn_type]
        print(f"{turn_type.title()}-turn:")
        for _, row in data.iterrows():
            print(f"  {row['refusals_allowed']} refusals: ASR = {row['asr_mean']:.3f} ± {row['asr_std']:.3f}")
    
    plt.show()

if __name__ == '__main__':
    main() 