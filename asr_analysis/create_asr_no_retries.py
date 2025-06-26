#!/usr/bin/env python3
"""
Variant 1: ASR analysis with NO retries allowed.
If the target model refuses on the first attempt, the score is 0 regardless of subsequent attempts.
This script reads directly from JSONL files instead of using master_results.csv.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Optional

def load_jsonl_file(file_path: str) -> Dict:
    """
    Load a JSONL file and extract metadata and conversation data.
    
    Args:
        file_path (str): Path to the JSONL file
        
    Returns:
        Dict: Dictionary containing metadata and conversation data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        if not lines:
            return None
            
        # First line contains metadata
        metadata = json.loads(lines[0].strip())
        
        # Subsequent lines contain conversation rounds
        conversation_data = []
        for line in lines[1:]:
            if line.strip():
                conversation_data.append(json.loads(line.strip()))
        
        return {
            'metadata': metadata,
            'conversation': conversation_data
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def analyze_no_retries_score(conversation_data: List[Dict]) -> float:
    """
    Analyze conversation data with no retries policy.
    If the first attempt results in a refusal, return 0.
    Otherwise, return the maximum score achieved.
    
    Args:
        conversation_data: List of conversation rounds
        
    Returns:
        float: Score (0 if first attempt was refused, otherwise max score)
    """
    if not conversation_data:
        return 0.0
    
    # Find the first non-metadata entry
    first_response = None
    for entry in conversation_data:
        if 'score' in entry and 'round' in entry:
            first_response = entry
            break
    
    if not first_response:
        return 0.0
    
    # If first response was a refusal, return 0
    if first_response.get('score') == 'refused':
        return 0.0
    
    # Otherwise, find the maximum score across all rounds
    max_score = 0.0
    for entry in conversation_data:
        if 'score' in entry and entry['score'] != 'refused':
            try:
                score = float(entry['score'])
                max_score = max(max_score, score)
            except (ValueError, TypeError):
                continue
    
    return max_score

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

def extract_data_from_jsonl_files(root_directory: str, tactic_filter: str = None) -> pd.DataFrame:
    """
    Extract data from all JSONL files in a directory and analyze with no-retries policy.
    
    Args:
        root_directory (str): Root directory path to search for JSONL files
        tactic_filter (str): Optional filter for specific jailbreak tactic
        
    Returns:
        pd.DataFrame: DataFrame with analyzed results
    """
    results = []
    
    # Find all JSONL files
    root_path = Path(root_directory)
    jsonl_files = list(root_path.rglob('*.jsonl'))
    
    print(f"Found {len(jsonl_files)} JSONL files to process...")
    
    for file_path in jsonl_files:
        data = load_jsonl_file(str(file_path))
        if not data:
            continue
            
        metadata = data['metadata']
        conversation = data['conversation']
        
        # Apply tactic filter if specified
        if tactic_filter and metadata.get('jailbreak_tactic') != tactic_filter:
            continue
        
        # Calculate no-retries score
        score = analyze_no_retries_score(conversation)
        
        # Store result
        results.append({
            'target_model': metadata.get('target_model'),
            'test_case': metadata.get('test_case'),
            'turn_type': metadata.get('turn_type'),
            'jailbreak_tactic': metadata.get('jailbreak_tactic'),
            'score': score,
            'file_path': str(file_path)
        })
    
    df = pd.DataFrame(results)
    print(f"Successfully processed {len(df)} files")
    return df

def create_plot(results_df, title, filename):
    """Create and save a stacked horizontal bar chart."""
    if len(results_df) == 0:
        print(f"No data found for {filename}!")
        return
    
    # Sort by total ASR (multi-turn) for better visualization
    results_df = results_df.sort_values('multi_asr', ascending=True)
    
    # Create the stacked horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
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

def analyze_data(df, tactic_filter=None):
    """Analyze data with no-retries scoring method."""
    
    # Apply tactic filter if specified
    if tactic_filter:
        df_filtered = df[df['jailbreak_tactic'] == tactic_filter].copy()
        print(f"After filtering for {tactic_filter}: {len(df_filtered)} experiments")
    else:
        df_filtered = df.copy()
        print(f"Using all tactics: {len(df_filtered)} experiments")
    
    # Define the models we want to analyze
    target_models = [
        'gpt-4o-mini-2024-07-18',
        'meta-llama/llama-3.1-8b-instruct', 
        'meta-llama/llama-3.1-70b-instruct',
        'meta-llama/llama-3.2-1b-instruct',
        'meta-llama/llama-3.2-3b-instruct',
        'anthropic/claude-3.5-sonnet',
        'anthropic/claude-3.7-sonnet', 
        'google/gemini-2.0-flash-lite-001',
        'qwen/qwen3-8b'
    ]
    
    # Filter for target models
    df_filtered = df_filtered[df_filtered['target_model'].isin(target_models)].copy()
    print(f"After filtering for target models: {len(df_filtered)} experiments")
    
    results = []
    
    for model in target_models:
        model_data = df_filtered[df_filtered['target_model'] == model]
        
        if len(model_data) == 0:
            print(f"No data for {model}")
            continue
            
        print(f"\nAnalyzing {model}:")
        
        # Calculate ASR for single and multi-turn
        single_turn = model_data[model_data['turn_type'] == 'single']
        multi_turn = model_data[model_data['turn_type'] == 'multi']
        
        # For no-retries, we average the max scores directly (continuous values)
        single_asr = single_turn['score'].mean() if len(single_turn) > 0 else 0.0
        multi_asr = multi_turn['score'].mean() if len(multi_turn) > 0 else 0.0
        
        print(f"  Single-turn: {len(single_turn)} experiments, ASR = {single_asr:.3f}")
        print(f"  Multi-turn: {len(multi_turn)} experiments, ASR = {multi_asr:.3f}")
        
        results.append({
            'model': model,
            'model_clean': get_clean_model_name(model),
            'single_asr': single_asr,
            'multi_asr': multi_asr,
            'multi_only_asr': max(0, multi_asr - single_asr)  # For stacking
        })
    
    return pd.DataFrame(results)

def main():
    # Define the root directories to search
    root_directories = [
        '/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch3A',
        '/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch2B',
        '/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch2C',
        '/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch2D',
        '/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch_1',
    ]
    
    # Combine data from all directories
    all_dfs = []
    for root_dir in root_directories:
        if os.path.exists(root_dir):
            df = extract_data_from_jsonl_files(root_dir)
            all_dfs.append(df)
    
    if not all_dfs:
        print("No data found in specified directories!")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\nCombined dataset: {len(combined_df)} total experiments")
    
    # Define variants to create (direct_request only)
    variants = [
        {
            'tactic_filter': 'direct_request',
            'title': 'Attack Success Rate (No Retries): Single-turn vs Multi-turn\n(Direct Request Tactic, Max Score)',
            'filename': 'asr_no_retries_direct_request.png'
        }
    ]
    
    # Generate each variant
    for i, variant in enumerate(variants, 1):
        print(f"\n{'='*60}")
        print(f"Creating variant {i}/{len(variants)}: {variant['filename']}")
        print(f"{'='*60}")
        
        results_df = analyze_data(combined_df, variant['tactic_filter'])
        
        # Filter out models with no data
        results_df = results_df[(results_df['single_asr'] > 0) | (results_df['multi_asr'] > 0)]
        
        create_plot(results_df, variant['title'], variant['filename'])
        
        # Print summary statistics
        if len(results_df) > 0:
            print(f"\nSummary Statistics:")
            print(f"Average Single-turn ASR: {results_df['single_asr'].mean():.3f}")
            print(f"Average Multi-turn ASR: {results_df['multi_asr'].mean():.3f}")
            print(f"Models with higher Multi-turn ASR: {sum(results_df['multi_asr'] > results_df['single_asr'])}/{len(results_df)}")

if __name__ == "__main__":
    main()