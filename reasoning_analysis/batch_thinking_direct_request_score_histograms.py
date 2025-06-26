#!/usr/bin/env python3
"""
Score Histograms by Reasoning Token Bins - Batch Thinking + Direct Request
Creates histograms of maximum scores for different reasoning token bins
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_batch_thinking_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load all JSONL files from batch_thinking directory, filtered for direct_request tactic"""
    data_dir = Path(data_dir)
    all_data = []
    
    print("Loading data from", data_dir)
    print("Filtering for batch_thinking data and direct_request tactic only")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Filter for direct_request tactic only
                    jailbreak_tactic = data.get('jailbreak_tactic', '').lower()
                    if jailbreak_tactic != 'direct_request':
                        continue
                    
                    # Extract reasoning tokens
                    reasoning_tokens = 0
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                    
                    # Extract success score - treat scores not between 0 and 1 as 0
                    success_score = data.get('score', 0)
                    try:
                        success_score = float(success_score)
                        if not (0 <= success_score <= 1):
                            success_score = 0
                    except (ValueError, TypeError):
                        success_score = 0
                    
                    # Extract goal achieved
                    goal_achieved = data.get('goal_achieved', False)
                    
                    # Extract reasoning level from filename
                    reasoning_level = 'unknown'
                    if 'reasoning_high' in file_path.name:
                        reasoning_level = 'high'
                    elif 'reasoning_medium' in file_path.name:
                        reasoning_level = 'medium'
                    elif 'reasoning_low' in file_path.name:
                        reasoning_level = 'low'
                    elif 'reasoning_none' in file_path.name:
                        reasoning_level = 'none'
                    
                    # Extract other metadata for understanding score computation
                    record = {
                        'file': file_path.name,
                        'reasoning_tokens': reasoning_tokens,
                        'success_score': success_score,
                        'goal_achieved': goal_achieved,
                        'reasoning_level': reasoning_level,
                        'model': data.get('target_model', 'unknown'),
                        'test_case': data.get('test_case', 'unknown'),
                        'round': data.get('round', 1),
                        'turn_type': data.get('turn_type', 'unknown'),
                        # Score computation related fields
                        'target_response': str(data.get('target_response', ''))[:200],  # First 200 chars for inspection
                        'rejected': data.get('rejected', False),
                        'evaluation_method': data.get('evaluation_method', 'unknown')
                    }
                    
                    all_data.append(record)
                    
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(all_data)} records with direct_request tactic")
    return pd.DataFrame(all_data)

def aggregate_by_conversation(df):
    """Aggregate data by conversation to get maximum scores per conversation"""
    
    print("\nAggregating by conversation...")
    
    # Group by file (conversation) and get max score and average reasoning tokens
    conversation_data = []
    
    for file_name in df['file'].unique():
        file_data = df[df['file'] == file_name]
        
        # Get maximum score for this conversation
        max_score = file_data['success_score'].max()
        
        # Get average reasoning tokens (only counting non-zero tokens)
        reasoning_tokens = file_data[file_data['reasoning_tokens'] > 0]['reasoning_tokens']
        avg_reasoning_tokens = reasoning_tokens.mean() if len(reasoning_tokens) > 0 else 0
        
        # Get other metadata
        conversation_record = {
            'file': file_name,
            'max_score': max_score,
            'avg_reasoning_tokens': avg_reasoning_tokens,
            'reasoning_level': file_data['reasoning_level'].iloc[0],
            'model': file_data['model'].iloc[0],
            'test_case': file_data['test_case'].iloc[0],
            'num_turns': len(file_data)
        }
        
        conversation_data.append(conversation_record)
    
    conv_df = pd.DataFrame(conversation_data)
    print(f"Aggregated into {len(conv_df)} conversations")
    
    return conv_df

def create_reasoning_token_bins(df):
    """Create reasoning token bins and analyze score distributions"""
    
    print("\nCreating reasoning token bins...")
    
    # Define bins
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Create bins
    df['reasoning_bin'] = pd.cut(df['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Print bin statistics
    print("\nBin Statistics:")
    for label in bin_labels:
        bin_data = df[df['reasoning_bin'] == label]
        if len(bin_data) > 0:
            print(f"{label}: n={len(bin_data)}, avg_score={bin_data['max_score'].mean():.3f}, "
                  f"success_rate={(bin_data['max_score'] >= 1.0).mean()*100:.1f}%")
    
    return df, bin_labels

def create_score_histograms(df, bin_labels):
    """Create histograms of maximum scores for each reasoning token bin"""
    
    print("\nGenerating score histograms...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Define colors for each bin
    colors = ['red', 'orange', 'gold', 'lightgreen', 'darkgreen']
    
    # Plot histogram for each bin
    for i, (label, color) in enumerate(zip(bin_labels, colors)):
        ax = axes[i]
        bin_data = df[df['reasoning_bin'] == label]
        
        if len(bin_data) > 0:
            scores = bin_data['max_score']
            
            # Create histogram
            ax.hist(scores, bins=20, alpha=0.7, color=color, edgecolor='black', density=True)
            ax.set_xlabel('Maximum Score')
            ax.set_ylabel('Density')
            ax.set_title(f'Score Distribution: {label} Reasoning Tokens\n(n={len(bin_data)})')
            ax.set_xlim(0, 1)
            ax.grid(True, alpha=0.3)
            
            # Add statistics
            mean_score = scores.mean()
            success_rate = (scores >= 1.0).mean() * 100
            ax.axvline(mean_score, color='red', linestyle='--', alpha=0.8, linewidth=2)
            ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
                   transform=ax.transAxes, verticalalignment='top', 
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                   horizontalalignment='center', verticalalignment='center')
            ax.set_title(f'Score Distribution: {label} Reasoning Tokens\n(n=0)')
    
    # Overall distribution in the last subplot
    ax = axes[5]
    all_scores = df['max_score']
    ax.hist(all_scores, bins=20, alpha=0.7, color='blue', edgecolor='black', density=True)
    ax.set_xlabel('Maximum Score')
    ax.set_ylabel('Density')
    ax.set_title(f'Overall Score Distribution\n(n={len(df)})')
    ax.set_xlim(0, 1)
    ax.grid(True, alpha=0.3)
    
    # Add overall statistics
    mean_score = all_scores.mean()
    success_rate = (all_scores >= 1.0).mean() * 100
    ax.axvline(mean_score, color='red', linestyle='--', alpha=0.8, linewidth=2)
    ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
           transform=ax.transAxes, verticalalignment='top', 
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('batch_thinking_direct_request_score_histograms.png', dpi=300, bbox_inches='tight')
    plt.show()

def analyze_score_computation(df):
    """Analyze how scores are computed by examining the data"""
    
    print("\n=== SCORE COMPUTATION ANALYSIS ===")
    
    # Look at unique values of score
    unique_scores = sorted(df['success_score'].unique())
    print(f"Unique score values found: {unique_scores}")
    
    # Count frequency of each score
    score_counts = df['success_score'].value_counts().sort_index()
    print("\nScore frequency distribution:")
    for score, count in score_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  Score {score}: {count} occurrences ({percentage:.1f}%)")
    
    # Look at relationship between score and goal_achieved
    print("\nRelationship between score and goal_achieved:")
    cross_tab = pd.crosstab(df['success_score'], df['goal_achieved'], margins=True)
    print(cross_tab)
    
    # Examine some examples of different scores
    print("\nExamples of different score values:")
    for score in [0.0, 0.5, 1.0]:
        if score in df['success_score'].values:
            examples = df[df['success_score'] == score].head(3)
            print(f"\nScore {score} examples:")
            for _, row in examples.iterrows():
                print(f"  File: {row['file']}")
                print(f"  Goal achieved: {row['goal_achieved']}")
                print(f"  Rejected: {row['rejected']}")
                print(f"  Response preview: {row['target_response'][:100]}...")
                print()

def main():
    """Main analysis function"""
    
    print("Starting Score Histogram Analysis for Batch Thinking + Direct Request...")
    
    # Load data
    df = load_batch_thinking_data()
    
    if len(df) == 0:
        print("No data found!")
        return
    
    # Analyze score computation
    analyze_score_computation(df)
    
    # Aggregate by conversation
    conv_df = aggregate_by_conversation(df)
    
    # Create reasoning token bins
    conv_df, bin_labels = create_reasoning_token_bins(conv_df)
    
    # Create histograms
    create_score_histograms(conv_df, bin_labels)
    
    print("\nAnalysis complete! Histograms saved as 'batch_thinking_direct_request_score_histograms.png'")

if __name__ == "__main__":
    main()