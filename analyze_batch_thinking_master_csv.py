#!/usr/bin/env python3
"""
Analyze batch_thinking data from master_results.csv to replicate asr_reasoning.png analysis.
This version works with the full 2,217 experiments and extracts reasoning token data from source files.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import glob
import ast
import os
from pathlib import Path

def safe_eval_scores(scores_str):
    """Safely evaluate scores string to list."""
    try:
        if pd.isna(scores_str):
            return []
        return ast.literal_eval(scores_str)
    except:
        return []

def calculate_max_score(scores_list):
    """Calculate maximum score from list of scores."""
    if not scores_list:
        return 0.0
    return max(scores_list)

def extract_reasoning_tokens_from_jsonl(file_path):
    """Extract reasoning token information from JSONL source file."""
    reasoning_tokens = []
    total_tokens = 0
    
    if not os.path.exists(file_path):
        return 0, 0
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines[1:]:  # Skip first line (experiment metadata)
            if line.strip():
                data = json.loads(line)
                
                # Extract reasoning tokens if available
                if 'token_usage' in data and data['token_usage'].get('available'):
                    token_info = data['token_usage']
                    if 'reasoning_tokens' in token_info and token_info['reasoning_tokens'] > 0:
                        reasoning_tokens.append(token_info['reasoning_tokens'])
                    if 'total_tokens' in token_info:
                        total_tokens += token_info['total_tokens']
                        
    except Exception as e:
        return 0, 0
    
    avg_reasoning_tokens = np.mean(reasoning_tokens) if reasoning_tokens else 0
    return avg_reasoning_tokens, total_tokens

def load_batch_thinking_data():
    """Load and process batch_thinking data from master CSV with reasoning token extraction."""
    
    # Load master CSV (clean version)
    df = pd.read_csv('/home/dcruz/multi_turn_jailbreaks/csv_results/master_results_verified_clean.csv')
    
    # Filter for batch_thinking data
    df_batch = df[df['batch'] == 'batch_thinking'].copy()
    print(f"Found {len(df_batch)} batch_thinking experiments")
    
    # Parse scores and calculate max score
    df_batch['scores_list'] = df_batch['scores'].apply(safe_eval_scores)
    df_batch['max_score'] = df_batch['scores_list'].apply(calculate_max_score)
    
    # Use ALL batch_thinking experiments - extract reasoning info from filenames or other sources
    df_reasoning = df_batch.copy()
    print(f"Using all {len(df_reasoning)} batch_thinking experiments")
    
    # Extract reasoning level from source_file if available
    def extract_reasoning_from_source(row):
        source_file = row['source_file']
        reasoning_col = row['reasoning']
        
        # First check if reasoning column has explicit value
        if pd.notna(reasoning_col) and reasoning_col in ['low', 'medium', 'high']:
            return reasoning_col
        
        # Otherwise try to extract from source filename
        if pd.notna(source_file):
            if 'reasoning_low' in str(source_file):
                return 'low'
            elif 'reasoning_medium' in str(source_file):
                return 'medium'
            elif 'reasoning_high' in str(source_file):
                return 'high'
        
        # If we can't determine reasoning level, try to infer from other patterns
        # For now, return unknown
        return 'unknown'
    
    df_reasoning['reasoning_level'] = df_reasoning.apply(extract_reasoning_from_source, axis=1)
    print(f"Reasoning level distribution: {df_reasoning['reasoning_level'].value_counts()}")
    
    # Extract reasoning token information from source files
    reasoning_token_data = []
    
    for idx, row in df_reasoning.iterrows():
        source_file = row['source_file']
        
        # Try to find the source JSONL file
        if pd.notna(source_file):
            # Try different possible paths
            possible_paths = [
                f"/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs/batch_thinking/{row['jailbreak_tactic']}/{source_file}",
                f"/home/dcruz/multi_turn_jailbreaks/clean_results/test/batch_thinking_test/{row['jailbreak_tactic']}/{source_file}",
                f"/home/dcruz/multi_turn_jailbreaks/clean_results/{source_file}"
            ]
            
            avg_reasoning_tokens = 0
            total_tokens = 0
            
            for path in possible_paths:
                if os.path.exists(path):
                    avg_reasoning_tokens, total_tokens = extract_reasoning_tokens_from_jsonl(path)
                    break
            
            reasoning_token_data.append({
                'avg_reasoning_tokens': avg_reasoning_tokens,
                'total_tokens': total_tokens
            })
        else:
            reasoning_token_data.append({
                'avg_reasoning_tokens': 0,
                'total_tokens': 0
            })
    
    # Add reasoning token data to dataframe
    token_df = pd.DataFrame(reasoning_token_data)
    df_reasoning = pd.concat([df_reasoning.reset_index(drop=True), token_df], axis=1)
    
    # Calculate conversation length (number of rounds)
    df_reasoning['conversation_length'] = df_reasoning['max_round']
    
    print(f"Token extraction complete. Average reasoning tokens per conversation: {df_reasoning['avg_reasoning_tokens'].mean():.2f}")
    
    return df_reasoning

def create_asr_reasoning_plots(df):
    """Create the 6-subplot analysis matching asr_reasoning.png"""
    
    # Filter for multi-turn data (as shown in the original image)
    df_multi = df[df['turn_type'] == 'multi'].copy()
    print(f"Multi-turn experiments for analysis: {len(df_multi)}")
    
    # Create figure with 2x3 subplots
    fig = plt.figure(figsize=(15, 10))
    
    # 1. Top left: Average Reasoning Tokens vs Maximum Score scatter plot
    ax1 = plt.subplot(2, 3, 1)
    
    # Create scatter plot
    scatter = ax1.scatter(df_multi['avg_reasoning_tokens'], df_multi['max_score'], 
                         alpha=0.6, s=30, color='steelblue')
    
    # Add trend line (if we have enough data and variation)
    if len(df_multi) > 1 and df_multi['avg_reasoning_tokens'].var() > 0:
        try:
            z = np.polyfit(df_multi['avg_reasoning_tokens'], df_multi['max_score'], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(df_multi['avg_reasoning_tokens'].min(), 
                                 df_multi['avg_reasoning_tokens'].max(), 100)
            ax1.plot(x_trend, p(x_trend), "r--", alpha=0.8)
        except np.linalg.LinAlgError:
            print("Warning: Could not fit trend line due to insufficient data variation")
    
    ax1.set_xlabel('Average Reasoning Tokens per Conversation')
    ax1.set_ylabel('Maximum Score')
    ax1.set_title('Average Reasoning Tokens vs Maximum Score (Multi-turn)')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.0)
    
    # 2. Top right: Average Maximum Score by Reasoning Level
    ax2 = plt.subplot(2, 3, 2)
    
    # Get available reasoning levels in the data
    available_levels = df_multi['reasoning_level'].value_counts()
    reasoning_levels = []
    colors = []
    
    # Define preferred order and colors
    level_order = ['low', 'medium', 'high', 'unknown']
    level_colors = {'low': 'orange', 'medium': 'yellow', 'high': 'green', 'unknown': 'gray'}
    
    for level in level_order:
        if level in available_levels.index:
            reasoning_levels.append(level)
            colors.append(level_colors[level])
    
    avg_scores = []
    counts = []
    
    for level in reasoning_levels:
        level_data = df_multi[df_multi['reasoning_level'] == level]
        avg_score = level_data['max_score'].mean() if len(level_data) > 0 else 0
        avg_scores.append(avg_score)
        counts.append(len(level_data))
    
    bars = ax2.bar(reasoning_levels, avg_scores, color=colors, alpha=0.8)
    
    # Add count labels and score labels
    for i, (bar, count, score) in enumerate(zip(bars, counts, avg_scores)):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{score:.3f}\n(n={count})', ha='center', va='bottom', fontsize=10)
    
    ax2.set_ylabel('Average Maximum Score')
    ax2.set_title('Average Maximum Score by Reasoning Level (Multi-turn)')
    ax2.set_ylim(0, 1.0)
    
    # 3. Middle left: Distribution of Maximum Scores
    ax3 = plt.subplot(2, 3, 3)
    
    # Create histogram
    ax3.hist(df_multi['max_score'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
    
    # Add vertical line for goal achieved (score >= 0.5)
    ax3.axvline(x=0.5, color='red', linestyle='--', alpha=0.8, label='Goal Achieved (≥ 0.5)')
    
    ax3.set_xlabel('Maximum Score')
    ax3.set_ylabel('Number of Conversations')
    ax3.set_title('Distribution of Maximum Scores (Multi-turn)')
    ax3.legend()
    
    # 4. Middle right: Success Rate by Reasoning Level
    ax4 = plt.subplot(2, 3, 4)
    
    success_rates = []
    for level in reasoning_levels:
        level_data = df_multi[df_multi['reasoning_level'] == level]
        # Success defined as max_score >= 0.5 OR goal_achieved = True
        success_rate = ((level_data['max_score'] >= 0.5) | (level_data['goal_achieved'])).mean() * 100
        success_rates.append(success_rate)
    
    bars = ax4.bar(reasoning_levels, success_rates, color=colors, alpha=0.8)
    
    # Add percentage labels
    for bar, rate in zip(bars, success_rates):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax4.set_ylabel('Success Rate (%)')
    ax4.set_title('Success Rate by Reasoning Level (Multi-turn)\n(max_score ≥ 0.5, goal achieved)')
    ax4.set_ylim(0, 100)
    
    # 5. Bottom left: Success Rate & Avg Max Score by Token Ranges
    ax5 = plt.subplot(2, 3, 5)
    ax5_twin = ax5.twinx()
    
    # Create token range bins - more granular for 200-500 range where most data lies
    df_multi['token_range'] = pd.cut(df_multi['avg_reasoning_tokens'], 
                                   bins=[0, 100, 200, 300, 400, 500, 750, 1000, np.inf],
                                   labels=['0-100', '100-200', '200-300', '300-400', '400-500', '500-750', '750-1000', '1000+'])
    
    token_ranges = ['0-100', '100-200', '200-300', '300-400', '400-500', '500-750', '750-1000', '1000+']
    success_rates_by_tokens = []
    avg_scores_by_tokens = []
    counts_by_tokens = []
    
    for token_range in token_ranges:
        range_data = df_multi[df_multi['token_range'] == token_range]
        if len(range_data) > 0:
            success_rate = ((range_data['max_score'] >= 0.5) | (range_data['goal_achieved'])).mean() * 100
            avg_score = range_data['max_score'].mean()
            count = len(range_data)
        else:
            success_rate = 0
            avg_score = 0
            count = 0
        
        success_rates_by_tokens.append(success_rate)
        avg_scores_by_tokens.append(avg_score)
        counts_by_tokens.append(count)
    
    # Plot bars and line
    x_pos = range(len(token_ranges))
    bars = ax5.bar(x_pos, success_rates_by_tokens, color='lightcoral', alpha=0.7, label='Success Rate (%)')
    line = ax5_twin.plot(x_pos, avg_scores_by_tokens, 'bo-', label='Avg Max Score', linewidth=2, markersize=8)
    
    # Add labels
    for i, (bar, rate, count) in enumerate(zip(bars, success_rates_by_tokens, counts_by_tokens)):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{rate:.1f}%\n(n={count})', ha='center', va='bottom', fontsize=9)
    
    for i, score in enumerate(avg_scores_by_tokens):
        if score > 0:
            ax5_twin.text(i, score + 0.05, f'{score:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax5.set_xlabel('Average Reasoning Tokens per Conversation')
    ax5.set_ylabel('Success Rate (%)', color='red')
    ax5_twin.set_ylabel('Average Maximum Score', color='blue')
    ax5.set_title('Success Rate & Avg Max Score by Token Ranges (Multi-turn)')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(token_ranges, rotation=45)
    ax5.set_ylim(0, 100)
    ax5_twin.set_ylim(0, 1.0)
    
    # 6. Bottom right: Average Reasoning Tokens by Maximum Score Bins
    ax6 = plt.subplot(2, 3, 6)
    
    # Create score bins
    df_multi['score_bin'] = pd.cut(df_multi['max_score'], 
                                 bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                 labels=['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'])
    
    score_bins = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
    avg_tokens_by_score = []
    counts_by_score = []
    
    for score_bin in score_bins:
        bin_data = df_multi[df_multi['score_bin'] == score_bin]
        avg_tokens = bin_data['avg_reasoning_tokens'].mean() if len(bin_data) > 0 else 0
        count = len(bin_data)
        avg_tokens_by_score.append(avg_tokens)
        counts_by_score.append(count)
    
    bars = ax6.bar(range(len(score_bins)), avg_tokens_by_score, color='mediumseagreen', alpha=0.8)
    
    # Add labels
    max_tokens = max(avg_tokens_by_score) if avg_tokens_by_score else 1
    for i, (bar, tokens, count) in enumerate(zip(bars, avg_tokens_by_score, counts_by_score)):
        if count > 0:
            ax6.text(i, bar.get_height() + max_tokens * 0.02,
                    f'{int(tokens)}\n(n={count})', ha='center', va='bottom', fontsize=9)
    
    ax6.set_xlabel('Maximum Score Bins')
    ax6.set_ylabel('Average Reasoning Tokens')
    ax6.set_title('Average Reasoning Tokens by Maximum Score Bins (Multi-turn)')
    ax6.set_xticks(range(len(score_bins)))
    ax6.set_xticklabels(score_bins, rotation=45)
    
    plt.tight_layout(pad=2.0)
    
    return fig

def main():
    """Main analysis function."""
    print("Loading batch_thinking data from master CSV...")
    
    # Load batch_thinking data with reasoning token extraction
    df_reasoning = load_batch_thinking_data()
    
    if df_reasoning.empty:
        print("No reasoning data found!")
        return
    
    print(f"\nLoaded {len(df_reasoning)} experiments with reasoning data")
    print(f"Reasoning levels: {df_reasoning['reasoning_level'].value_counts()}")
    print(f"Turn types: {df_reasoning['turn_type'].value_counts()}")
    print(f"Tactics: {df_reasoning['jailbreak_tactic'].value_counts()}")
    print(f"Models: {df_reasoning['target_model'].value_counts()}")
    
    # Create the comprehensive analysis plots
    fig = create_asr_reasoning_plots(df_reasoning)
    
    # Save the plot
    output_path = '/home/dcruz/multi_turn_jailbreaks/asr_reasoning_analysis_full_clean.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nAnalysis saved to: {output_path}")
    
    # Save the processed data
    df_reasoning.to_csv('/home/dcruz/multi_turn_jailbreaks/batch_thinking_reasoning_data_clean.csv', index=False)
    print("Data saved to: batch_thinking_reasoning_data_clean.csv")
    
    # Print summary statistics
    multi_turn = df_reasoning[df_reasoning['turn_type'] == 'multi']
    print(f"\nSummary Statistics:")
    print(f"Total experiments: {len(df_reasoning)}")
    print(f"Multi-turn experiments: {len(multi_turn)}")
    print(f"Average reasoning tokens per conversation: {df_reasoning['avg_reasoning_tokens'].mean():.1f}")
    print(f"Average max score: {df_reasoning['max_score'].mean():.3f}")
    print(f"Overall success rate: {((df_reasoning['max_score'] >= 0.5) | (df_reasoning['goal_achieved'])).mean() * 100:.1f}%")
    
    # Reasoning level analysis
    print(f"\nBy Reasoning Level (Multi-turn):")
    available_levels = multi_turn['reasoning_level'].value_counts().index
    for level in ['low', 'medium', 'high', 'unknown']:
        if level in available_levels:
            level_data = multi_turn[multi_turn['reasoning_level'] == level]
            if len(level_data) > 0:
                avg_score = level_data['max_score'].mean()
                success_rate = ((level_data['max_score'] >= 0.5) | (level_data['goal_achieved'])).mean() * 100
                avg_tokens = level_data['avg_reasoning_tokens'].mean()
                print(f"  {level}: n={len(level_data)}, avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, avg_tokens={avg_tokens:.1f}")
    
    plt.show()

if __name__ == "__main__":
    main()