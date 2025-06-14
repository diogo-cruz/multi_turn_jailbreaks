#!/usr/bin/env python3
"""
Heatmap of test cases vs tactics for single and multi-turn attacks.
Creates separate heatmaps for each model or average across models.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
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

def create_heatmap_data(df, models_to_plot=None, aggregate=False):
    """
    Create heatmap data for test cases vs tactics
    
    Args:
        df: Filtered dataframe
        models_to_plot: List of models to include, or None for all
        aggregate: If True, aggregate across all models
    """
    if models_to_plot is None:
        # Get models with sufficient data
        model_counts = df.groupby('target_model').size()
        models_to_plot = model_counts[model_counts >= 50].index.tolist()[:10]  # Top 10 models with enough data
    
    heatmap_data = {}
    
    if aggregate:
        # Create aggregated heatmap across all models
        for turn_type in ['single', 'multi']:
            df_turn = df[df['turn_type'] == turn_type].copy()
            
            # Calculate ASR for each test case x tactic combination
            asr_matrix = df_turn.groupby(['test_case', 'jailbreak_tactic'])['goal_achieved'].mean().unstack(fill_value=0)
            
            # Filter to test cases and tactics with sufficient data
            test_case_counts = df_turn['test_case'].value_counts()
            tactic_counts = df_turn['jailbreak_tactic'].value_counts()
            
            valid_test_cases = test_case_counts[test_case_counts >= 20].index.tolist()[:15]  # Top 15 test cases
            valid_tactics = tactic_counts[tactic_counts >= 20].index.tolist()
            
            asr_matrix = asr_matrix.loc[
                asr_matrix.index.isin(valid_test_cases), 
                asr_matrix.columns.isin(valid_tactics)
            ]
            
            heatmap_data[f'aggregate_{turn_type}'] = asr_matrix
    
    else:
        # Create heatmaps for individual models
        for model in models_to_plot:
            df_model = df[df['target_model'] == model].copy()
            
            for turn_type in ['single', 'multi']:
                df_turn = df_model[df_model['turn_type'] == turn_type].copy()
                
                if len(df_turn) < 10:  # Skip if too little data
                    continue
                
                # Calculate ASR for each test case x tactic combination
                asr_matrix = df_turn.groupby(['test_case', 'jailbreak_tactic'])['goal_achieved'].mean().unstack(fill_value=0)
                
                # Only keep combinations with at least 2 samples
                count_matrix = df_turn.groupby(['test_case', 'jailbreak_tactic']).size().unstack(fill_value=0)
                asr_matrix = asr_matrix.where(count_matrix >= 2, np.nan)
                
                model_short = model.split('/')[-1] if '/' in model else model
                heatmap_data[f'{model_short}_{turn_type}'] = asr_matrix
    
    return heatmap_data

def create_heatmap_plot(heatmap_data, title_suffix=""):
    """
    Create heatmap plot from heatmap data
    """
    n_heatmaps = len(heatmap_data)
    
    if n_heatmaps == 0:
        print("No heatmap data to plot")
        return None
    
    # Determine subplot layout
    if n_heatmaps <= 2:
        ncols = 2
        nrows = 1
    elif n_heatmaps <= 4:
        ncols = 2
        nrows = 2
    elif n_heatmaps <= 6:
        ncols = 3
        nrows = 2
    else:
        ncols = 4
        nrows = (n_heatmaps + 3) // 4
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(5*ncols, 4*nrows))
    
    if nrows == 1 and ncols == 1:
        axes = [axes]
    elif nrows == 1 or ncols == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    
    for i, (key, data) in enumerate(heatmap_data.items()):
        if i >= len(axes):
            break
            
        ax = axes[i]
        
        if data.empty:
            ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=14)
            ax.set_title(key.replace('_', ' ').title())
            continue
        
        # Create heatmap
        sns.heatmap(data, ax=ax, cmap='YlOrRd', vmin=0, vmax=1, 
                   annot=True, fmt='.2f', cbar_kws={'label': 'ASR'},
                   square=False, linewidths=0.5)
        
        ax.set_title(key.replace('_', ' ').title())
        ax.set_xlabel('Jailbreak Tactic')
        ax.set_ylabel('Test Case')
        
        # Rotate x-axis labels for better readability
        ax.tick_params(axis='x', rotation=45)
        ax.tick_params(axis='y', rotation=0)
    
    # Hide unused subplots
    for i in range(len(heatmap_data), len(axes)):
        axes[i].set_visible(False)
    
    plt.suptitle(f'ASR Heatmaps: Test Cases vs Tactics{title_suffix}', fontsize=16, y=0.98)
    plt.tight_layout()
    
    return fig

def create_aggregated_heatmap(df):
    """
    Create a single aggregated heatmap comparing single vs multi-turn
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    for i, turn_type in enumerate(['single', 'multi']):
        ax = ax1 if i == 0 else ax2
        
        df_turn = df[df['turn_type'] == turn_type].copy()
        
        # Calculate ASR for each test case x tactic combination
        asr_matrix = df_turn.groupby(['test_case', 'jailbreak_tactic'])['goal_achieved'].mean().unstack(fill_value=0)
        count_matrix = df_turn.groupby(['test_case', 'jailbreak_tactic']).size().unstack(fill_value=0)
        
        # Filter to combinations with sufficient data
        min_samples = 10
        asr_matrix = asr_matrix.where(count_matrix >= min_samples, np.nan)
        
        # Get top test cases and tactics by frequency
        test_case_counts = df_turn['test_case'].value_counts()
        tactic_counts = df_turn['jailbreak_tactic'].value_counts()
        
        top_test_cases = test_case_counts.head(15).index.tolist()
        top_tactics = tactic_counts.head(10).index.tolist()
        
        # Filter matrix
        asr_matrix_filtered = asr_matrix.loc[
            asr_matrix.index.isin(top_test_cases),
            asr_matrix.columns.isin(top_tactics)
        ]
        
        # Create heatmap
        sns.heatmap(asr_matrix_filtered, ax=ax, cmap='YlOrRd', vmin=0, vmax=1,
                   annot=True, fmt='.2f', cbar_kws={'label': 'ASR'},
                   square=False, linewidths=0.5)
        
        ax.set_title(f'{turn_type.title()}-turn Attacks')
        ax.set_xlabel('Jailbreak Tactic')
        ax.set_ylabel('Test Case' if i == 0 else '')
        
        # Format labels
        tactic_labels = [t.replace('_', ' ').title() for t in asr_matrix_filtered.columns]
        ax.set_xticklabels(tactic_labels, rotation=45, ha='right')
        
        if i == 1:  # Remove y-labels for second plot
            ax.set_yticklabels([])
    
    plt.suptitle('Attack Success Rate: Test Cases vs Tactics\n(Aggregated across models)', 
                 fontsize=16, y=0.95)
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
    
    # Analyze data distribution
    print("\nData distribution:")
    print("==================")
    
    model_counts = df_filtered['target_model'].value_counts()
    print(f"Number of models: {len(model_counts)}")
    print("Top 10 models by sample count:")
    for model, count in model_counts.head(10).items():
        model_short = model.split('/')[-1] if '/' in model else model
        print(f"  {model_short}: {count}")
    
    tactic_counts = df_filtered['jailbreak_tactic'].value_counts()
    print(f"\nTactics ({len(tactic_counts)}):")
    for tactic, count in tactic_counts.items():
        print(f"  {tactic}: {count}")
    
    test_case_counts = df_filtered['test_case'].value_counts()
    print(f"\nTest cases ({len(test_case_counts)}):")
    for test_case, count in test_case_counts.head(15).items():
        print(f"  {test_case}: {count}")
    
    # Create output directory
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    
    # Create aggregated heatmap
    print("\nCreating aggregated heatmap...")
    fig_agg = create_aggregated_heatmap(df_filtered)
    fig_agg.savefig(output_dir / 'heatmap_testcases_tactics_aggregated.pdf', dpi=300, bbox_inches='tight')
    fig_agg.savefig(output_dir / 'heatmap_testcases_tactics_aggregated.png', dpi=300, bbox_inches='tight')
    print(f"Aggregated heatmap saved to {output_dir / 'heatmap_testcases_tactics_aggregated.pdf'}")
    
    # Create individual model heatmaps
    print("\nCreating individual model heatmaps...")
    
    # Get top models with sufficient data
    model_counts = df_filtered.groupby('target_model').size()
    top_models = model_counts[model_counts >= 50].index.tolist()[:6]  # Top 6 models
    
    if len(top_models) > 0:
        heatmap_data = create_heatmap_data(df_filtered, top_models, aggregate=False)
        
        if len(heatmap_data) > 0:
            fig_models = create_heatmap_plot(heatmap_data, f" (Top {len(top_models)} Models)")
            if fig_models:
                fig_models.savefig(output_dir / 'heatmap_testcases_tactics_by_model.pdf', dpi=300, bbox_inches='tight')
                fig_models.savefig(output_dir / 'heatmap_testcases_tactics_by_model.png', dpi=300, bbox_inches='tight')
                print(f"Model-specific heatmaps saved to {output_dir / 'heatmap_testcases_tactics_by_model.pdf'}")
        else:
            print("No sufficient data for individual model heatmaps")
    else:
        print("No models with sufficient data for individual heatmaps")
    
    # Summary statistics
    print("\nSummary Statistics:")
    print("==================")
    
    # ASR by turn type
    asr_by_turn = df_filtered.groupby('turn_type')['goal_achieved'].mean()
    print("Overall ASR by turn type:")
    for turn_type, asr in asr_by_turn.items():
        print(f"  {turn_type}: {asr:.3f}")
    
    # ASR by tactic
    asr_by_tactic = df_filtered.groupby(['jailbreak_tactic', 'turn_type'])['goal_achieved'].mean().unstack()
    print("\nASR by tactic:")
    print(asr_by_tactic.round(3))
    
    # Test case difficulty (based on overall ASR)
    test_case_asr = df_filtered.groupby('test_case')['goal_achieved'].mean().sort_values()
    print(f"\nMost difficult test cases (lowest ASR):")
    for test_case, asr in test_case_asr.head(10).items():
        print(f"  {test_case}: {asr:.3f}")
    
    print(f"\nEasiest test cases (highest ASR):")
    for test_case, asr in test_case_asr.tail(10).items():
        print(f"  {test_case}: {asr:.3f}")
    
    plt.show()

if __name__ == '__main__':
    main() 