#!/usr/bin/env python3
"""
Create custom ASR figure with horizontal bar chart
- Uses professional styling with LaTeX fonts
- Blue/orange color scheme with transparency
- Handles special case for single-turn data starting with "refused"
- Generates both PNG and PDF output
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
    """Clean model names for better display (matching LOGBOOK specifications)."""
    name_mapping = {
        'deepseek/deepseek-chat-v3-0324': 'Deepseek Chat V3',
        'openai/gpt-4.1': 'GPT-4.1',
        'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
        'openai/gpt-4.1-nano': 'GPT-4.1 Nano',
        'openai/gpt-4o': 'GPT-4o',
        'openai/gpt-4o-2024-05-13': 'GPT-4o (old)',
        'google/gemini-2.5-pro-preview-03-25': 'Gemini 2.5 Pro',
        'google/gemini-2.5-pro': 'Gemini 2.5 Pro',
        'google/gemini-2.5-flash-preview': 'Gemini 2.5 Flash',
        'google/gemini-2.5-flash': 'Gemini 2.5 Flash',
        'google/gemini-2.5-flash-lite-preview-06-17': 'Gemini 2.5 Flash Lite',
        'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
        'anthropic/claude-3.7-sonnet': 'Claude 3.7 Sonnet',
        'anthropic/claude-3-sonnet': 'Claude 3 Sonnet',
        'anthropic/claude-sonnet-4': 'Claude Sonnet 4',
        'meta-llama/llama-3.1-8b-instruct': 'Llama 3.1 8B',
        'meta-llama/llama-3.1-70b-instruct': 'Llama 3.1 70B', 
        'meta-llama/llama-3.2-1b-instruct': 'Llama 3.2 1B',
        'meta-llama/llama-3.2-3b-instruct': 'Llama 3.2 3B',
        'google/gemini-2.0-flash-lite-001': 'Gemini 2.0 Flash Lite',
        'qwen/qwen3-8b': 'Qwen3 8B'
    }
    return name_mapping.get(model_name, model_name)

def create_custom_three_scenario_figure(data_file):
    """Create custom ASR figure with three scenarios as stacked bars."""
    
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
    plt.savefig('custom_asr_figure_batch7.png', dpi=300, bbox_inches='tight')
    plt.savefig('custom_asr_figure_batch7.pdf', bbox_inches='tight')
    
    print("Custom ASR figure saved as:")
    print("- custom_asr_figure_batch7.png (300 DPI)")
    print("- custom_asr_figure_batch7.pdf (vector format)")
    
    plt.close()

def load_and_process_jsonl_data(data_dir="clean_results/final_runs/batch7"):
    """Load and process JSONL files with refusal handling"""
    import json
    from pathlib import Path
    
    data_dir = Path(data_dir)
    all_data = []
    
    print(f"Loading JSONL data from {data_dir}")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                continue
                
            # Extract metadata from first line
            try:
                metadata_line = json.loads(lines[0].strip())
                file_metadata = {
                    'target_model': metadata_line.get('target_model', 'unknown'),
                    'test_case': metadata_line.get('test_case', 'unknown'),
                    'turn_type': metadata_line.get('turn_type', 'unknown'),
                    'jailbreak_tactic': metadata_line.get('jailbreak_tactic', 'unknown'),
                }
            except json.JSONDecodeError as e:
                print(f"Error parsing metadata in {file_path}: {e}")
                continue
            
            # Only process direct_request and command tactics (matching original script)
            if file_metadata['jailbreak_tactic'] not in ['direct_request', 'command']:
                continue
            
            # Exclude fake_online_profile test case (data isn't good)
            if file_metadata['test_case'] == 'fake_online_profile':
                continue
                
            # Process data lines (skip metadata line)
            data_lines = lines[1:]
            
            # Collect scores for this conversation
            conversation_scores = []
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Extract score
                    score = data.get('score')
                    if score is not None:
                        conversation_scores.append(score)
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
            
            # Add to all_data if we have scores
            if conversation_scores:
                record = {
                    'file': file_path.name,
                    'scores': conversation_scores,
                    **file_metadata
                }
                all_data.append(record)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(all_data)} conversations with scores")
    return all_data

def analyze_jsonl_data_with_three_scenarios(data_list):
    """
    Analyze JSONL data with three scenarios:
    1. Single-turn with original logic (refusals ignored, use max score)
    2. Single-turn with refusal handling (refusals -> 0.0)
    3. Multi-turn (unchanged)
    """
    
    # Group by model and turn type
    model_data = {}
    
    for record in data_list:
        model = record['target_model']
        turn_type = record['turn_type']
        scores = record['scores']
        
        if model not in model_data:
            model_data[model] = {'single': [], 'multi': []}
        
        model_data[model][turn_type].append(scores)
    
    results = []
    
    for model, data in model_data.items():
        print(f"\nAnalyzing {model}:")
        
        # Process single-turn data - ORIGINAL METHOD (ignore refusals, use max)
        single_original_scores = []
        for scores_list in data['single']:
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
        for scores_list in data['single']:
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
        for scores_list in data['multi']:
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

def analyze_csv_data_with_refusal_handling(df, tactic_filter='direct_request'):
    """
    Analyze CSV data with special handling for single-turn refusal cases.
    This processes the raw scores from master_results.csv, not pre-computed ASR values.
    """
    
    # Apply tactic filter
    df_filtered = df[df['jailbreak_tactic'] == tactic_filter].copy()
    print(f"After filtering for {tactic_filter}: {len(df_filtered)} experiments")
    
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
        
        # Process single-turn data with refusal handling
        single_scores = []
        refused_count = 0
        for _, row in single_turn.iterrows():
            scores_list = row['scores_list']
            # Apply refusal handling: if first score is "refused", use 0.0
            if (len(scores_list) > 0 and 
                isinstance(scores_list[0], str) and 
                scores_list[0].lower() == "refused"):
                single_scores.append(0.0)
                refused_count += 1
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
                single_scores.append(max_score)
        
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
        
        single_asr = np.mean(single_scores) if single_scores else 0.0
        multi_asr = np.mean(multi_scores) if multi_scores else 0.0
        
        print(f"  Single-turn: {len(single_scores)} experiments, {refused_count} with refusal handling, avg score = {single_asr:.3f}")
        print(f"  Multi-turn: {len(multi_scores)} experiments, avg score = {multi_asr:.3f}")
        
        results.append({
            'model': model,
            'model_clean': get_clean_model_name(model),
            'single_asr': single_asr,
            'multi_asr': multi_asr,
            'multi_only_asr': max(0, multi_asr - single_asr)
        })
    
    return pd.DataFrame(results)

def main():
    """Main function to create the modified custom ASR figure with three scenarios for batch7."""
    
    print("Creating custom ASR figure with three scenarios for batch7...")
    print("=" * 60)
    
    # Process JSONL data from batch7 with three scenarios
    jsonl_data = load_and_process_jsonl_data("clean_results/final_runs/batch7")
    
    if not jsonl_data:
        print("No JSONL data found!")
        return
    
    # Analyze with three scenarios
    results_df = analyze_jsonl_data_with_three_scenarios(jsonl_data)
    
    # Filter out models with no data (check any of the three scenarios)
    results_df = results_df[(results_df['single_original_asr'] > 0) | 
                           (results_df['single_refusal_handled_asr'] > 0) | 
                           (results_df['multi_asr'] > 0)]
    
    if len(results_df) == 0:
        print("No results after processing!")
        return
    
    # Save the processed data
    output_data_file = 'asr_three_scenarios_batch7_data.csv'
    results_df.to_csv(output_data_file, index=False)
    print(f"Processed data saved to: {output_data_file}")
    
    # Create the figure
    create_custom_three_scenario_figure(output_data_file)
    
    print("=" * 60)
    print("Custom ASR figure creation complete!")

if __name__ == "__main__":
    main()