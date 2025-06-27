#!/usr/bin/env python3
"""
Create custom line plot of StrongREJECT score vs reasoning tokens
- Scatter plot with connected lines for each model
- Different colors for each model
- Dashed lines for single-turn, solid lines for multi-turn
- LaTeX font, 24px font size, no title
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib

# Enable LaTeX rendering
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.size'] = 24

def clean_model_name(raw_model_name):
    """Clean up model names for display"""
    if not raw_model_name or raw_model_name == 'unknown':
        return 'unknown'
    
    # Remove provider prefixes and extract main model name
    model_name = raw_model_name.lower()
    
    if 'claude' in model_name:
        return 'Claude'
    elif 'gemini' in model_name:
        return 'Gemini'
    elif 'gpt' in model_name or 'o1-mini' in model_name or 'o3-mini' in model_name or 'o4-mini' in model_name:
        return 'OpenAI'
    elif 'qwen' in model_name:
        return 'Qwen'
    else:
        # Return the part after the slash if it exists, otherwise the whole name
        if '/' in raw_model_name:
            return raw_model_name.split('/')[-1].title()
        return raw_model_name.title()

def load_and_process_data(data_dir="clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
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
                    'model': clean_model_name(metadata_line.get('target_model', 'unknown')),
                    'test_case': metadata_line.get('test_case', 'unknown'),
                    'turn_type': metadata_line.get('turn_type', 'unknown'),
                    'jailbreak_tactic': metadata_line.get('jailbreak_tactic', 'unknown'),
                }
            except json.JSONDecodeError as e:
                print(f"Error parsing metadata in {file_path}: {e}")
                continue
                
            # Process data lines (skip metadata line)
            data_lines = lines[1:]
            
            # Collect data for this JSONL file
            conversation_scores = []
            conversation_reasoning_tokens = []
            valid_data_found = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Only process if this matches our target tactics
                    jailbreak_tactic = data.get('jailbreak_tactic', file_metadata['jailbreak_tactic']).lower()
                    if jailbreak_tactic in ['direct_request', 'command']:
                        valid_data_found = True
                    
                    # Extract score - treat scores not between 0 and 1 as 0
                    if data.get('score') is not None:
                        try:
                            score = float(data['score'])
                            if not (0 <= score <= 1):
                                score = 0
                            conversation_scores.append(score)
                        except (ValueError, TypeError):
                            conversation_scores.append(0)
                    
                    # Extract reasoning tokens
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                        if reasoning_tokens > 0:
                            conversation_reasoning_tokens.append(reasoning_tokens)
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
            # Only include conversations with valid tactic and scores
            if valid_data_found and conversation_scores:
                # Maximum score across all rounds
                max_score = max(conversation_scores)
                
                # Average reasoning tokens (only counting non-zero tokens)
                avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
                
                conversation_record = {
                    'file': file_path.name,
                    'max_score': max_score,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'num_rounds': len(conversation_scores),
                    **file_metadata
                }
                
                # Separate by turn type
                turn_type = file_metadata.get('turn_type', 'unknown')
                if turn_type == 'single' or 'single_turn' in file_path.name:
                    single_turn_data.append(conversation_record)
                elif turn_type == 'multi' or 'multi_turn' in file_path.name:
                    multi_turn_data.append(conversation_record)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(single_turn_data)} single-turn conversations")
    print(f"Loaded {len(multi_turn_data)} multi-turn conversations")
    
    return pd.DataFrame(single_turn_data), pd.DataFrame(multi_turn_data)

def create_reasoning_token_bins(df, model):
    """Create reasoning token bins for a specific model"""
    
    model_data = df[df['model'] == model].copy()
    
    if len(model_data) == 0:
        return []
    
    # Define bins (same as in the original)
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    bin_centers = [100, 350, 750, 1500, 3000]  # Centers for plotting
    
    # Create bins
    model_data['reasoning_bin'] = pd.cut(model_data['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Calculate bin statistics
    bin_stats = []
    for i, label in enumerate(bin_labels):
        bin_data = model_data[model_data['reasoning_bin'] == label]
        if len(bin_data) > 0:
            avg_score = bin_data['max_score'].mean()
            count = len(bin_data)
            bin_stats.append({
                'bin': label,
                'bin_center': bin_centers[i],
                'avg_score': avg_score,
                'count': count
            })
    
    return bin_stats

def create_line_plot(single_df, multi_df):
    """Create the custom line plot"""
    
    # Get models with sufficient data
    single_models = []
    multi_models = []
    
    for model in single_df['model'].value_counts().index:
        if single_df['model'].value_counts()[model] >= 10:
            single_models.append(model)
    
    for model in multi_df['model'].value_counts().index:
        if multi_df['model'].value_counts()[model] >= 10:
            multi_models.append(model)
    
    # Get all unique models
    all_models = list(set(single_models + multi_models))
    
    # Define colors for each model
    colors = plt.cm.Set1(np.linspace(0, 1, len(all_models)))
    model_colors = dict(zip(all_models, colors))
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot single-turn data (dashed lines)
    for model in single_models:
        bin_stats = create_reasoning_token_bins(single_df, model)
        if len(bin_stats) > 1:  # Need at least 2 points for a line
            x_vals = [stat['bin_center'] for stat in bin_stats]
            y_vals = [stat['avg_score'] for stat in bin_stats]
            
            ax.plot(x_vals, y_vals, 
                   color=model_colors[model], 
                   linestyle='--', 
                   marker='o', 
                   markersize=8,
                   linewidth=2,
                   label=f'{model} (single)' if model not in multi_models else None)
    
    # Plot multi-turn data (solid lines)
    for model in multi_models:
        bin_stats = create_reasoning_token_bins(multi_df, model)
        if len(bin_stats) > 1:  # Need at least 2 points for a line
            x_vals = [stat['bin_center'] for stat in bin_stats]
            y_vals = [stat['avg_score'] for stat in bin_stats]
            
            ax.plot(x_vals, y_vals, 
                   color=model_colors[model], 
                   linestyle='-', 
                   marker='o', 
                   markersize=8,
                   linewidth=2,
                   label=f'{model} (multi)' if model not in single_models else None)
    
    # Customize the plot
    ax.set_xlabel('Reasoning Tokens')
    ax.set_ylabel('StrongREJECT score')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    # Create single legend with separate model colors and line styles
    legend_handles = []
    
    # Add model color entries (using points)
    for model in all_models:
        legend_handles.append(plt.Line2D([0], [0], color=model_colors[model], marker='o', markersize=8, 
                                       linestyle='', label=model))
    
    # Add line style entries
    legend_handles.append(plt.Line2D([0], [0], color='black', linestyle='--', linewidth=2, label='single'))
    legend_handles.append(plt.Line2D([0], [0], color='black', linestyle='-', linewidth=2, label='multi'))
    
    ax.legend(handles=legend_handles, loc='lower right')
    
    plt.tight_layout()
    plt.savefig('strongreject_vs_reasoning_tokens.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function"""
    
    print("Creating custom line plot...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Create the plot
    create_line_plot(single_df, multi_df)
    
    print("Plot saved as 'strongreject_vs_reasoning_tokens.png'")

if __name__ == "__main__":
    main()