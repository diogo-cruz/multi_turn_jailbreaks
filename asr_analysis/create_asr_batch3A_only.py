#!/usr/bin/env python3
"""
Create ASR plot for batch3A only, using direct_request tactic.
This matches the analysis done in the notebook.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ast
import os

def safe_eval_scores(scores_str):
    """Safely evaluate scores string to list."""
    try:
        if pd.isna(scores_str):
            return []
        return ast.literal_eval(scores_str)
    except:
        return []

def calculate_max_score(scores_list):
    """Return the maximum score from the list (non-binary)."""
    if not scores_list:
        return 0.0
    return max(scores_list)

def get_clean_model_name(model_name):
    """Clean model names for better display."""
    name_mapping = {
        'gpt-4o-mini-2024-07-18': 'GPT-4o Mini',
        'meta-llama/llama-3.1-8b-instruct': 'Llama 3.1 8B',
        'meta-llama/llama-3.1-70b-instruct': 'Llama 3.1 70B', 
        'meta-llama/llama-3.2-1b-instruct': 'Llama 3.2 1B',
        'meta-llama/llama-3.2-3b-instruct': 'Llama 3.2 3B',
        'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
        'anthropic/claude-3.7-sonnet': 'Claude 3.7 Sonnet',
        'google/gemini-2.0-flash-lite-001': 'Gemini 2.0 Flash Lite',
        'qwen/qwen3-8b': 'Qwen3 8B'
    }
    return name_mapping.get(model_name, model_name)

def create_plot(results_df, title, filename):
    """Create and save a stacked horizontal bar chart."""
    if len(results_df) == 0:
        print(f"No data found for {filename}!")
        return
    
    # Sort by total ASR (multi-turn) for better visualization
    results_df = results_df.sort_values('multi_asr', ascending=True)
    
    # Create the stacked horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, max(8, len(results_df) * 0.5)))
    
    models = results_df['model_clean'].values
    single_asr = results_df['single_asr'].values
    multi_only_asr = results_df['multi_only_asr'].values
    
    # Create stacked bars
    bars1 = ax.barh(models, single_asr, label='Single-turn ASR', 
                   color='lightblue', alpha=0.8)
    bars2 = ax.barh(models, multi_only_asr, left=single_asr, 
                   label='Additional Multi-turn ASR', color='darkblue', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Attack Success Rate (ASR)', fontsize=12)
    ax.set_ylabel('Models', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.set_xlim(0, 1.0)
    ax.grid(axis='x', alpha=0.3)
    
    # Add value labels on bars
    for i, (single, multi_total) in enumerate(zip(single_asr, single_asr + multi_only_asr)):
        if single > 0.01:
            ax.text(single/2, i, f'{single:.2f}', ha='center', va='center', 
                   fontweight='bold', color='white')
        if multi_total > single + 0.01:
            ax.text(single + (multi_total - single)/2, i, f'{multi_total:.2f}', 
                   ha='center', va='center', fontweight='bold', color='white')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = f'/home/dcruz/multi_turn_jailbreaks/asr_analysis/{filename}'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to: {output_path}")
    
    # Save the data
    data_filename = filename.replace('.png', '_data.csv')
    results_df.to_csv(f'/home/dcruz/multi_turn_jailbreaks/asr_analysis/{data_filename}', index=False)
    print(f"Data saved to: {data_filename}")
    
    plt.close()

def analyze_data(df, tactic_filter='direct_request'):
    """Analyze data with max score method for direct_request tactic, using ALL models."""
    
    # Apply tactic filter
    df_filtered = df[df['jailbreak_tactic'] == tactic_filter].copy()
    print(f"After filtering for {tactic_filter}: {len(df_filtered)} experiments")
    
    # Get ALL unique models in the data (no filtering)
    all_models = df_filtered['target_model'].unique()
    print(f"Found {len(all_models)} unique models in the data")
    
    # Parse scores and calculate ASR for each experiment
    df_filtered['scores_list'] = df_filtered['scores'].apply(safe_eval_scores)
    df_filtered['score'] = df_filtered['scores_list'].apply(calculate_max_score)
    
    results = []
    
    for model in all_models:
        model_data = df_filtered[df_filtered['target_model'] == model]
        
        if len(model_data) == 0:
            print(f"No data for {model}")
            continue
            
        print(f"\nAnalyzing {model}:")
        
        # Standard approach: average all experiments directly
        single_turn = model_data[model_data['turn_type'] == 'single']
        multi_turn = model_data[model_data['turn_type'] == 'multi']
        
        single_asr = single_turn['score'].mean() if len(single_turn) > 0 else 0.0
        multi_asr = multi_turn['score'].mean() if len(multi_turn) > 0 else 0.0
        
        print(f"  Single-turn: {len(single_turn)} experiments, avg max score = {single_asr:.3f}")
        print(f"  Multi-turn: {len(multi_turn)} experiments, avg max score = {multi_asr:.3f}")
        
        results.append({
            'model': model,
            'model_clean': get_clean_model_name(model),
            'single_asr': single_asr,
            'multi_asr': multi_asr,
            'multi_only_asr': max(0, multi_asr - single_asr)  # For stacking
        })
    
    return pd.DataFrame(results)

def main():
    # Load the master CSV (using regular version instead of verified)
    df_full = pd.read_csv('/home/dcruz/multi_turn_jailbreaks/csv_results/master_results.csv')
    print(f"Loaded {len(df_full)} total experiments")
    
    # Filter for only batch3A to match notebook analysis
    target_batch = 'batch3A'
    df = df_full[df_full['batch'] == target_batch].copy()
    print(f"After filtering for batch {target_batch}: {len(df)} experiments")
    
    if len(df) == 0:
        print("No data found after batch filtering!")
        return
    
    print(f"\n{'='*60}")
    print(f"Creating ASR plot for batch3A models only")
    print(f"{'='*60}")
    
    results_df = analyze_data(df, tactic_filter='direct_request')
    
    # Filter out models with no data
    results_df = results_df[(results_df['single_asr'] > 0) | (results_df['multi_asr'] > 0)]
    
    create_plot(
        results_df, 
        'Attack Success Rate: Single-turn vs Multi-turn\n(Direct Request Tactic, Max Score Average) - Batch3A Only',
        'asr_max_score_direct_request_batch3A_only.png'
    )
    
    # Print summary statistics
    if len(results_df) > 0:
        print(f"\nSummary Statistics:")
        print(f"Total models analyzed: {len(results_df)}")
        print(f"Average Single-turn ASR: {results_df['single_asr'].mean():.3f}")
        print(f"Average Multi-turn ASR: {results_df['multi_asr'].mean():.3f}")
        print(f"Models with higher Multi-turn ASR: {sum(results_df['multi_asr'] > results_df['single_asr'])}/{len(results_df)}")
        
        # Print list of all models
        print(f"\nModels included:")
        for model in sorted(results_df['model'].values):
            print(f"  - {model}")

if __name__ == "__main__":
    main()