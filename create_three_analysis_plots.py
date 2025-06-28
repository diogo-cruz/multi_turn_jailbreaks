#!/usr/bin/env python3
"""
Create three analysis plots:
1. Qwen-specific overlapping bar chart (single/multi swapped)
2. Test case comparison analysis (PDF version)
3. Score histograms (PDF version)
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

def create_reasoning_token_bins(df):
    """Create reasoning token bins for all models"""
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Use the same bins as before
    bin_edges = [0, 200, 500, 1000, 1500, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-1500', '1500+']
    
    # Create bins
    df = df.copy()
    df['reasoning_bin'] = pd.cut(df['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    return df

def plot1_qwen_overlapping_bars(single_df, multi_df):
    """Plot 1: Qwen-specific overlapping bar chart with swapped positions"""
    
    # Keep only Qwen data and exclude fake_online_profile
    single_df = single_df[(single_df['model'] == 'Qwen') & (single_df['test_case'] != 'fake_online_profile')]
    multi_df = multi_df[(multi_df['model'] == 'Qwen') & (multi_df['test_case'] != 'fake_online_profile')]
    
    # Create reasoning token bins
    single_df = create_reasoning_token_bins(single_df)
    multi_df = create_reasoning_token_bins(multi_df)
    
    # Remove rows with NaN bins
    single_df = single_df.dropna(subset=['reasoning_bin'])
    multi_df = multi_df.dropna(subset=['reasoning_bin'])
    
    # Check if we have sufficient data
    if len(single_df) < 10 and len(multi_df) < 10:
        print("Insufficient Qwen data for plotting")
        return
    
    # Calculate average scores by reasoning bin
    single_grouped = single_df.groupby(['reasoning_bin'])['max_score'].agg(['mean', 'std', 'count']).reset_index()
    single_grouped.columns = ['reasoning_bin', 'avg_score', 'std_score', 'count']
    
    multi_grouped = multi_df.groupby(['reasoning_bin'])['max_score'].agg(['mean', 'std', 'count']).reset_index()
    multi_grouped.columns = ['reasoning_bin', 'avg_score', 'std_score', 'count']
    
    # Pivot to get values
    single_pivot = single_grouped.set_index('reasoning_bin')['avg_score']
    multi_pivot = multi_grouped.set_index('reasoning_bin')['avg_score']
    
    # Define the order of reasoning bins
    bin_order = ['0-200', '200-500', '500-1000', '1000-1500', '1500+']
    single_pivot = single_pivot.reindex(bin_order, fill_value=0)
    multi_pivot = multi_pivot.reindex(bin_order, fill_value=0)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Set up bar positions
    x = np.arange(len(bin_order))
    bar_width = 0.6
    
    # Create overlapping bars - SWAPPED: multi behind, single in front
    ax.bar(x, multi_pivot.values, bar_width, 
           label='Qwen (multi)', color='C0', alpha=0.3)
    ax.bar(x, single_pivot.values, bar_width,
           label='Qwen (single)', color='C0', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Reasoning Tokens')
    ax.set_ylabel('StrongREJECT score')
    ax.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(bin_order)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Legend with only Qwen
    legend_handles = [plt.Rectangle((0,0),1,1, color='C0', alpha=0.8, label='Qwen')]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=20)
    
    plt.tight_layout()
    plt.savefig('qwen_reasoning_tokens_overlapping_bars.pdf', dpi=300, bbox_inches='tight')
    plt.show()

def plot2_testcase_comparison(single_df, multi_df):
    """Plot 2: Test case comparison analysis"""
    
    # Combine data and exclude fake_online_profile
    combined_df = pd.concat([single_df, multi_df], ignore_index=True)
    combined_df = combined_df[combined_df['test_case'] != 'fake_online_profile']
    
    # Create reasoning token bins
    combined_df = create_reasoning_token_bins(combined_df)
    combined_df = combined_df.dropna(subset=['reasoning_bin'])
    
    # Get test cases and models
    test_cases = sorted(combined_df['test_case'].unique())
    models = sorted(combined_df['model'].unique())
    bin_order = ['0-200', '200-500', '500-1000', '1000-1500', '1500+']
    
    # Create subplot grid
    n_cases = len(test_cases)
    n_cols = 5  # Based on the original image
    n_rows = (n_cases + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows), sharex=True, sharey=True)
    axes = axes.flatten() if n_rows > 1 else [axes] if n_cols == 1 else axes
    
    # Plot each test case
    for i, test_case in enumerate(test_cases):
        if i >= len(axes):
            break
            
        ax = axes[i]
        test_data = combined_df[combined_df['test_case'] == test_case]
        
        # Group by model and reasoning bin
        grouped = test_data.groupby(['model', 'reasoning_bin'])['max_score'].mean().reset_index()
        
        # Create bars for each model
        x = np.arange(len(bin_order))
        bar_width = 0.8 / len(models)
        
        for j, model in enumerate(models):
            model_data = grouped[grouped['model'] == model]
            model_pivot = model_data.set_index('reasoning_bin')['max_score']
            model_pivot = model_pivot.reindex(bin_order, fill_value=0)
            
            x_pos = x + (j - len(models)/2 + 0.5) * bar_width
            ax.bar(x_pos, model_pivot.values, bar_width, 
                   label=model if i == 0 else None, 
                   color=f'C{j}', alpha=0.8)
        
        ax.set_title(test_case.replace('_', ' ').title(), fontsize=16)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')
        
        if i >= n_cases - n_cols:  # Bottom row
            ax.set_xticks(x)
            ax.set_xticklabels(bin_order, rotation=45, ha='right')
        
        if i % n_cols == 0:  # Left column
            ax.set_ylabel('StrongREJECT score')
    
    # Hide unused subplots
    for i in range(len(test_cases), len(axes)):
        axes[i].set_visible(False)
    
    # Add legend
    if len(test_cases) > 0:
        axes[0].legend(loc='upper left', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('testcase_comparison_analysis.pdf', dpi=300, bbox_inches='tight')
    plt.show()

def plot3_score_histograms(single_df, multi_df):
    """Plot 3: Score histograms by reasoning token bins"""
    
    # Exclude fake_online_profile
    single_df = single_df[single_df['test_case'] != 'fake_online_profile']
    multi_df = multi_df[multi_df['test_case'] != 'fake_online_profile']
    
    # Create reasoning token bins
    single_df = create_reasoning_token_bins(single_df)
    multi_df = create_reasoning_token_bins(multi_df)
    
    # Remove rows with NaN bins
    single_df = single_df.dropna(subset=['reasoning_bin'])
    multi_df = multi_df.dropna(subset=['reasoning_bin'])
    
    bin_order = ['0-200', '200-500', '500-1000', '1000-1500', '1500+']
    colors = ['red', 'orange', 'yellow', 'lightgreen', 'darkgreen']
    
    # Create subplot grid
    n_bins = len(bin_order)
    fig, axes = plt.subplots(2, n_bins, figsize=(20, 8), sharex=True, sharey=True)
    
    bins_edges = np.linspace(0, 1, 21)  # 20 bins from 0 to 1
    
    # Plot single-turn histograms (top row)
    for i, (bin_name, color) in enumerate(zip(bin_order, colors)):
        ax = axes[0, i]
        
        bin_data = single_df[single_df['reasoning_bin'] == bin_name]['max_score']
        
        if len(bin_data) > 0:
            ax.hist(bin_data, bins=bins_edges, color=color, alpha=0.7, density=True)
            
            # Add statistics
            mean_score = bin_data.mean()
            success_rate = (bin_data >= 0.5).mean() * 100
            
            ax.axvline(mean_score, color='blue', linestyle='--', linewidth=2)
            ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\\\\Success: {success_rate:.1f}\\%', 
                   transform=ax.transAxes, va='top', ha='left',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(f'Single-Turn: {bin_name} Tokens\\\\(n={len(bin_data)})', fontsize=16)
        ax.set_ylim(0, 6)
        ax.grid(True, alpha=0.3)
        
        if i == 0:
            ax.set_ylabel('Density')
    
    # Plot multi-turn histograms (bottom row)
    for i, (bin_name, color) in enumerate(zip(bin_order, colors)):
        ax = axes[1, i]
        
        bin_data = multi_df[multi_df['reasoning_bin'] == bin_name]['max_score']
        
        if len(bin_data) > 0:
            ax.hist(bin_data, bins=bins_edges, color=color, alpha=0.7, density=True)
            
            # Add statistics
            mean_score = bin_data.mean()
            success_rate = (bin_data >= 0.5).mean() * 100
            
            ax.axvline(mean_score, color='blue', linestyle='--', linewidth=2)
            ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\\\\Success: {success_rate:.1f}\\%', 
                   transform=ax.transAxes, va='top', ha='left',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(f'Multi-Turn: {bin_name} Tokens\\\\(n={len(bin_data)})', fontsize=16)
        ax.set_xlabel('Maximum Score')
        ax.set_ylim(0, 6)
        ax.grid(True, alpha=0.3)
        
        if i == 0:
            ax.set_ylabel('Density')
    
    plt.tight_layout()
    plt.savefig('score_histograms_by_reasoning_tokens.pdf', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function"""
    
    print("Creating three analysis plots...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    print("\\nCreating Plot 1: Qwen overlapping bars...")
    plot1_qwen_overlapping_bars(single_df, multi_df)
    
    print("\\nCreating Plot 2: Test case comparison...")
    plot2_testcase_comparison(single_df, multi_df)
    
    print("\\nCreating Plot 3: Score histograms...")
    plot3_score_histograms(single_df, multi_df)
    
    print("\\nAll plots saved as PDFs")

if __name__ == "__main__":
    main()