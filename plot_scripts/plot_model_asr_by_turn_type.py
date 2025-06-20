#!/usr/bin/env python3
"""
Plot Model ASR by Turn Type
Creates a plot showing Attack Success Rate (ASR) for each model, separated by single and multi-turn.
ASR is displayed on the x-axis with models on the y-axis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

def calculate_model_asr(df):
    """Calculate ASR for each model by turn type."""
    results = []
    
    for model in df['target_model'].unique():
        if pd.isna(model):
            continue
            
        model_data = df[df['target_model'] == model]
        model_short = model.split('/')[-1] if '/' in model else model
        
        for turn_type in ['single', 'multi']:
            turn_data = model_data[model_data['turn_type'] == turn_type]
            
            if len(turn_data) == 0:
                continue
                
            total_experiments = len(turn_data)
            successful_attacks = (turn_data['goal_achieved'] == 'True').sum()
            asr = (successful_attacks / total_experiments) * 100 if total_experiments > 0 else 0
            
            results.append({
                'model': model_short,
                'turn_type': turn_type,
                'total_experiments': total_experiments,
                'successful_attacks': successful_attacks,
                'asr': asr
            })
    
    return pd.DataFrame(results)

def create_asr_plot(asr_df):
    """Create horizontal bar plot with ASR on x-axis."""
    # Prepare data for plotting
    models = sorted(asr_df['model'].unique())
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, max(8, len(models) * 0.4)))
    
    # Prepare data for plotting
    single_data = asr_df[asr_df['turn_type'] == 'single'].set_index('model')['asr']
    multi_data = asr_df[asr_df['turn_type'] == 'multi'].set_index('model')['asr']
    
    # Create y positions for bars
    y_positions = np.arange(len(models))
    bar_height = 0.35
    
    # Create horizontal bars
    bars_single = ax.barh(y_positions - bar_height/2, 
                         [single_data.get(model, 0) for model in models],
                         bar_height, label='Single-turn', alpha=0.8, color='lightcoral')
    
    bars_multi = ax.barh(y_positions + bar_height/2,
                        [multi_data.get(model, 0) for model in models], 
                        bar_height, label='Multi-turn', alpha=0.8, color='lightblue')
    
    # Customize the plot
    ax.set_xlabel('Attack Success Rate (%)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Model', fontsize=12, fontweight='bold')
    ax.set_title('Attack Success Rate by Model and Turn Type', fontsize=14, fontweight='bold', pad=20)
    
    # Set y-axis
    ax.set_yticks(y_positions)
    ax.set_yticklabels(models)
    
    # Set x-axis
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    def add_value_labels(bars, data_series, models):
        for i, (bar, model) in enumerate(zip(bars, models)):
            value = data_series.get(model, 0)
            if value > 0:
                ax.text(value + 1, bar.get_y() + bar.get_height()/2, 
                       f'{value:.1f}%', ha='left', va='center', fontsize=9)
    
    add_value_labels(bars_single, single_data, models)
    add_value_labels(bars_multi, multi_data, models)
    
    # Add legend
    ax.legend(loc='lower right', framealpha=0.9)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

def create_summary_stats(asr_df, df):
    """Create summary statistics."""
    print("=" * 80)
    print("MODEL ASR ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_experiments = len(df)
    total_models = len(df['target_model'].unique())
    
    print(f"\nDataset Overview:")
    print(f"Total experiments: {total_experiments:,}")
    print(f"Total models: {total_models}")
    
    # Overall ASR by turn type
    overall_single = df[df['turn_type'] == 'single']
    overall_multi = df[df['turn_type'] == 'multi']
    
    single_asr = ((overall_single['goal_achieved'] == 'True').sum() / len(overall_single)) * 100 if len(overall_single) > 0 else 0
    multi_asr = ((overall_multi['goal_achieved'] == 'True').sum() / len(overall_multi)) * 100 if len(overall_multi) > 0 else 0
    
    print(f"\nOverall ASR:")
    print(f"Single-turn: {single_asr:.1f}% ({(overall_single['goal_achieved'] == 'True').sum():,}/{len(overall_single):,})")
    print(f"Multi-turn: {multi_asr:.1f}% ({(overall_multi['goal_achieved'] == 'True').sum():,}/{len(overall_multi):,})")
    
    # Top/bottom performers
    print(f"\nTop 5 Models (Single-turn ASR):")
    single_top = asr_df[asr_df['turn_type'] == 'single'].nlargest(5, 'asr')
    for _, row in single_top.iterrows():
        print(f"  {row['model']}: {row['asr']:.1f}% ({row['successful_attacks']}/{row['total_experiments']})")
    
    print(f"\nTop 5 Models (Multi-turn ASR):")
    multi_top = asr_df[asr_df['turn_type'] == 'multi'].nlargest(5, 'asr')
    for _, row in multi_top.iterrows():
        print(f"  {row['model']}: {row['asr']:.1f}% ({row['successful_attacks']}/{row['total_experiments']})")
    
    # Models with significant differences
    print(f"\nModels with Largest Single vs Multi-turn ASR Differences:")
    pivot_df = asr_df.pivot(index='model', columns='turn_type', values='asr').fillna(0)
    if 'single' in pivot_df.columns and 'multi' in pivot_df.columns:
        pivot_df['difference'] = pivot_df['single'] - pivot_df['multi']
        top_diff = pivot_df.nlargest(5, 'difference')
        for model, row in top_diff.iterrows():
            print(f"  {model}: Single {row['single']:.1f}% vs Multi {row['multi']:.1f}% (diff: +{row['difference']:.1f}pp)")

def main():
    # Load the master CSV
    csv_path = Path('csv_results/master_results_verified_clean.csv')
    if not csv_path.exists():
        print(f"Error: {csv_path} not found!")
        return
    
    print("Loading master CSV...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df):,} experiments")
    
    # Calculate ASR by model and turn type
    print("Calculating ASR by model and turn type...")
    asr_df = calculate_model_asr(df)
    
    # Create summary statistics
    create_summary_stats(asr_df, df)
    
    # Create the plot
    print("\nCreating ASR plot...")
    fig = create_asr_plot(asr_df)
    
    # Save the plot
    output_dir = Path('plot_outputs')
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / 'model_asr_by_turn_type.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Save data to CSV
    data_output_path = output_dir / 'model_asr_by_turn_type_data.csv'
    asr_df.to_csv(data_output_path, index=False)
    print(f"Data saved to: {data_output_path}")
    
    # Don't show the plot to avoid blocking
    # plt.show()

if __name__ == "__main__":
    main()