#!/usr/bin/env python3
"""
Create custom ASR figure with horizontal bar chart for batch1 data
- Uses professional styling with LaTeX fonts
- Blue/orange color scheme with transparency
- Handles special case for single-turn data starting with "refused"
- Generates both PNG and PDF output
- Processes batch1 CSV data with Llama models
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ast
import os

# Enable LaTeX rendering
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 24

def safe_eval_scores(scores_str):
    """Safely evaluate scores string to list."""
    try:
        if pd.isna(scores_str):
            return []
        return ast.literal_eval(scores_str)
    except:
        return []

def calculate_max_score_with_refusal_handling(scores_list):
    """
    Calculate maximum score with special handling for lists starting with "refused".
    For single-turn data: if scores start with "refused", return 0.0 instead of max score.
    For multi-turn data: use regular max score calculation.
    """
    if not scores_list:
        return 0.0
    
    # Check if first element is "refused" (case-insensitive)
    if (len(scores_list) > 0 and 
        isinstance(scores_list[0], str) and 
        scores_list[0].lower() == "refused"):
        return 0.0
    
    # Regular max calculation for other cases
    numeric_scores = []
    for score in scores_list:
        try:
            if isinstance(score, (int, float)):
                numeric_scores.append(score)
            elif isinstance(score, str) and score.lower() != "refused":
                numeric_scores.append(float(score))
        except ValueError:
            continue
    
    return max(numeric_scores) if numeric_scores else 0.0

def get_clean_model_name(model_name):
    """Clean model names for better display (batch1 models)."""
    name_mapping = {
        'gpt-4o-mini-2024-07-18': 'GPT-4o Mini',
        'meta-llama/llama-3.1-405b-instruct': 'Llama 3.1 405B',
        'meta-llama/llama-3.1-70b-instruct': 'Llama 3.1 70B',
        'meta-llama/llama-3.1-8b-instruct': 'Llama 3.1 8B',
        'meta-llama/llama-3.2-1b-instruct': 'Llama 3.2 1B',
        'meta-llama/llama-3.2-3b-instruct': 'Llama 3.2 3B',
        'meta-llama/llama-3.3-70b-instruct': 'Llama 3.3 70B'
    }
    return name_mapping.get(model_name, model_name)

def create_custom_three_scenario_figure(data_file):
    """Create custom ASR figure with three scenarios as overlapping bars."""
    
    # Read the data
    df = pd.read_csv(data_file)
    
    # Sort by multi-turn ASR for better visualization
    df = df.sort_values('multi_asr', ascending=True)
    
    # Create the figure (reduced height by 15%)
    fig, ax = plt.subplots(figsize=(12, max(6.8, len(df) * 0.425)))
    
    # Get data for plotting
    y_pos = np.arange(len(df))
    models = df['model_clean'].values
    single_refusal_handled_asr = df['single_refusal_handled_asr'].values
    single_original_asr = df['single_original_asr'].values
    multi_asr = df['multi_asr'].values
    
    # Create overlapping horizontal bars (stacked on same y-position)
    # Each bar shows the actual ASR value for that scenario
    
    # Create overlapping horizontal bars with professional styling
    # Order: largest first (multi), then medium (single), then smallest (single no refusals)
    # This ensures all bars are visible
    bars3 = ax.barh(y_pos, multi_asr, 
                   color='orange', alpha=0.7, label='multi')
    bars2 = ax.barh(y_pos, single_original_asr,
                   color='#1f77b4', alpha=0.7, label='single')
    bars1 = ax.barh(y_pos, single_refusal_handled_asr,
                   color='lightblue', alpha=0.7, label='single (no refusals)')
    
    # Customize the plot (following LOGBOOK specifications)
    ax.set_xlabel('StrongREJECT score')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(models)
    ax.set_xlim(0, max(1.0, max(single_original_asr.max(), multi_asr.max()) * 1.1))
    
    # Add professional grid and legend
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Remove title and y-axis label as specified in LOGBOOK
    # (Clean appearance for publication)
    
    plt.tight_layout()
    
    # Save both PNG and PDF formats
    plt.savefig('custom_asr_figure_batch1.png', dpi=300, bbox_inches='tight')
    plt.savefig('custom_asr_figure_batch1.pdf', bbox_inches='tight')
    
    print("Custom ASR figure saved as:")
    print("- custom_asr_figure_batch1.png (300 DPI)")
    print("- custom_asr_figure_batch1.pdf (vector format)")
    
    plt.close()

def analyze_csv_data_with_three_scenarios(df, tactic_filter='direct_request'):
    """
    Analyze CSV data with three scenarios for batch1:
    1. Single-turn with original logic (refusals ignored, use max score)
    2. Single-turn with refusal handling (refusals -> 0.0)  
    3. Multi-turn (unchanged)
    """
    
    # Apply tactic filter
    df_filtered = df[df['jailbreak_tactic'] == tactic_filter].copy()
    print(f"After filtering for {tactic_filter}: {len(df_filtered)} experiments")
    
    # Exclude fake_online_profile test case (data isn't good)
    df_filtered = df_filtered[df_filtered['test_case'] != 'fake_online_profile']
    print(f"After excluding fake_online_profile: {len(df_filtered)} experiments")
    
    # Get unique models
    all_models = df_filtered['target_model'].unique()
    print(f"Found {len(all_models)} unique models")
    
    # Parse scores
    df_filtered['scores_list'] = df_filtered['scores'].apply(safe_eval_scores)
    
    results = []
    
    for model in all_models:
        model_data = df_filtered[df_filtered['target_model'] == model]
        
        if len(model_data) == 0:
            continue
        
        print(f"\nAnalyzing {model}:")
        
        # Separate single-turn and multi-turn data
        single_turn = model_data[model_data['turn_type'] == 'single']
        multi_turn = model_data[model_data['turn_type'] == 'multi']
        
        # Process single-turn data - ORIGINAL METHOD (ignore refusals, use max)
        single_original_scores = []
        for _, row in single_turn.iterrows():
            scores_list = row['scores_list']
            # Original logic: extract all numeric scores, ignore "refused"
            numeric_scores = []
            for s in scores_list:
                try:
                    if isinstance(s, (int, float)):
                        numeric_scores.append(s)
                    elif isinstance(s, str) and s.lower() != "refused":
                        numeric_scores.append(float(s))
                except ValueError:
                    continue
            max_score = max(numeric_scores) if numeric_scores else 0.0
            single_original_scores.append(max_score)
        
        # Process single-turn data - WITH REFUSAL HANDLING
        single_refusal_handled_scores = []
        refused_count = 0
        for _, row in single_turn.iterrows():
            scores_list = row['scores_list']
            # Apply refusal handling: if first score is "refused", use 0.0
            if (len(scores_list) > 0 and 
                isinstance(scores_list[0], str) and 
                scores_list[0].lower() == "refused"):
                single_refusal_handled_scores.append(0.0)
                refused_count += 1
                print(f"  Found refused pattern: {scores_list} -> using 0.0")
            else:
                # Regular max calculation
                numeric_scores = []
                for s in scores_list:
                    try:
                        if isinstance(s, (int, float)):
                            numeric_scores.append(s)
                        elif isinstance(s, str) and s.lower() != "refused":
                            numeric_scores.append(float(s))
                    except ValueError:
                        continue
                max_score = max(numeric_scores) if numeric_scores else 0.0
                single_refusal_handled_scores.append(max_score)
        
        # Process multi-turn data (no special refusal handling)
        multi_scores = []
        for _, row in multi_turn.iterrows():
            scores_list = row['scores_list']
            numeric_scores = []
            for s in scores_list:
                try:
                    if isinstance(s, (int, float)):
                        numeric_scores.append(s)
                    elif isinstance(s, str) and s.lower() != "refused":
                        numeric_scores.append(float(s))
                except ValueError:
                    continue
            max_score = max(numeric_scores) if numeric_scores else 0.0
            multi_scores.append(max_score)
        
        single_original_asr = np.mean(single_original_scores) if single_original_scores else 0.0
        single_refusal_handled_asr = np.mean(single_refusal_handled_scores) if single_refusal_handled_scores else 0.0
        multi_asr = np.mean(multi_scores) if multi_scores else 0.0
        
        print(f"  Single-turn (original): {len(single_original_scores)} experiments, avg score = {single_original_asr:.3f}")
        print(f"  Single-turn (refusal handling): {len(single_refusal_handled_scores)} experiments, {refused_count} with refusal handling, avg score = {single_refusal_handled_asr:.3f}")
        print(f"  Multi-turn: {len(multi_scores)} experiments, avg score = {multi_asr:.3f}")
        
        results.append({
            'model': model,
            'model_clean': get_clean_model_name(model),
            'single_original_asr': single_original_asr,
            'single_refusal_handled_asr': single_refusal_handled_asr,
            'multi_asr': multi_asr
        })
    
    return pd.DataFrame(results)

def main():
    """Main function to create the modified custom ASR figure with three scenarios for batch1."""
    
    print("Creating custom ASR figure with three scenarios for batch1...")
    print("=" * 60)
    
    # Load batch1 CSV data
    batch1_csv_path = "csv_results/batch_1_results.csv"
    
    if not os.path.exists(batch1_csv_path):
        print(f"Error: {batch1_csv_path} not found!")
        return
    
    print(f"Loading data from {batch1_csv_path}")
    df = pd.read_csv(batch1_csv_path)
    print(f"Loaded {len(df)} total experiments")
    
    # Analyze with three scenarios
    results_df = analyze_csv_data_with_three_scenarios(df, tactic_filter='direct_request')
    
    # Filter out models with no data (check any of the three scenarios)
    results_df = results_df[(results_df['single_original_asr'] > 0) | 
                           (results_df['single_refusal_handled_asr'] > 0) | 
                           (results_df['multi_asr'] > 0)]
    
    if len(results_df) == 0:
        print("No results after processing!")
        return
    
    # Save the processed data
    output_data_file = 'asr_three_scenarios_batch1_data.csv'
    results_df.to_csv(output_data_file, index=False)
    print(f"Processed data saved to: {output_data_file}")
    
    # Create the figure
    create_custom_three_scenario_figure(output_data_file)
    
    print("=" * 60)
    print("Custom ASR figure creation complete!")

if __name__ == "__main__":
    main()