#!/usr/bin/env python3
"""
Replicate ASR vs Reasoning analysis from asr_reasoning.png
Analyzes batch_thinking data to show relationship between reasoning effort and attack success rates.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import glob
import ast
from pathlib import Path

def safe_eval_scores(scores_str):
    """Safely evaluate scores string to list."""
    try:
        if pd.isna(scores_str):
            return []
        return ast.literal_eval(scores_str)
    except:
        return []

def extract_reasoning_from_filename(filename):
    """Extract reasoning level from JSONL filename."""
    if 'reasoning_low' in filename:
        return 'low'
    elif 'reasoning_medium' in filename:
        return 'medium'  
    elif 'reasoning_high' in filename:
        return 'high'
    else:
        return None

def load_reasoning_data_from_jsonl():
    """Load reasoning token data from JSONL files."""
    reasoning_data = []
    
    # Find all batch_thinking JSONL files
    jsonl_pattern = "/home/dcruz/multi_turn_jailbreaks/clean_results/test/batch_thinking_test/**/*.jsonl"
    jsonl_files = glob.glob(jsonl_pattern, recursive=True)
    
    print(f"Found {len(jsonl_files)} JSONL files")
    
    for file_path in jsonl_files:
        reasoning_level = extract_reasoning_from_filename(file_path)
        if reasoning_level is None:
            continue
            
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            # Parse the experiment data from first line
            if len(lines) > 0:
                exp_data = json.loads(lines[0])
                
                # Parse conversation data and extract token info
                conversation_data = []
                reasoning_tokens = []
                
                for line in lines[1:]:
                    if line.strip():
                        data = json.loads(line)
                        conversation_data.append(data)
                        
                        # Extract reasoning tokens if available
                        if 'token_usage' in data and data['token_usage'].get('available'):
                            token_info = data['token_usage']
                            if 'reasoning_tokens' in token_info:
                                reasoning_tokens.append(token_info['reasoning_tokens'])
                
                # Get final goal achievement and scores
                goal_achieved = False
                max_score = 0.0
                scores = []
                
                for data in conversation_data:
                    if 'goal_achieved' in data:
                        goal_achieved = data['goal_achieved']
                    if 'score' in data and isinstance(data['score'], (int, float)):
                        scores.append(data['score'])
                        max_score = max(max_score, data['score'])
                
                # Calculate average reasoning tokens per conversation
                avg_reasoning_tokens = np.mean(reasoning_tokens) if reasoning_tokens else 0
                
                reasoning_data.append({
                    'target_model': exp_data.get('target_model', ''),
                    'test_case': exp_data.get('test_case', ''),
                    'turn_type': exp_data.get('turn_type', ''),
                    'jailbreak_tactic': exp_data.get('jailbreak_tactic', ''),
                    'reasoning_level': reasoning_level,
                    'goal_achieved': goal_achieved,
                    'max_score': max_score,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'total_reasoning_tokens': sum(reasoning_tokens) if reasoning_tokens else 0,
                    'conversation_length': len([d for d in conversation_data if 'round' in d])
                })
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return pd.DataFrame(reasoning_data)

def create_asr_reasoning_plots(df):
    """Create the 6-subplot analysis matching asr_reasoning.png"""
    
    # Filter for multi-turn data (as shown in the original image)
    df_multi = df[df['turn_type'] == 'multi'].copy()
    
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
    
    reasoning_levels = ['low', 'medium', 'high']
    colors = ['orange', 'yellow', 'green']
    
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
    
    # Create token range bins
    df_multi['token_range'] = pd.cut(df_multi['avg_reasoning_tokens'], 
                                   bins=[0, 500, 1000, 1500, 2000, np.inf],
                                   labels=['0-500', '500-1000', '1000-1500', '1500-2000', '2000+'])
    
    token_ranges = ['0-500', '500-1000', '1000-1500', '1500-2000', '2000+']
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
        ax5_twin.text(i, score + 0.05, f'{score:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax5.set_xlabel('Average Reasoning Tokens per Conversation')
    ax5.set_ylabel('Success Rate (%)', color='red')
    ax5_twin.set_ylabel('Average Maximum Score', color='blue')
    ax5.set_title('Success Rate & Avg Max Score by Token Ranges (Multi-turn)')
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(token_ranges, rotation=45)
    ax5.set_ylim(0, 70)
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
    for i, (bar, tokens, count) in enumerate(zip(bars, avg_tokens_by_score, counts_by_score)):
        if tokens > 0:
            ax6.text(i, bar.get_height() + max(avg_tokens_by_score) * 0.02,
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
    print("Loading reasoning data from JSONL files...")
    
    # Load reasoning data from JSONL files
    df_reasoning = load_reasoning_data_from_jsonl()
    
    if df_reasoning.empty:
        print("No reasoning data found!")
        return
    
    print(f"Loaded {len(df_reasoning)} experiments with reasoning data")
    print(f"Reasoning levels: {df_reasoning['reasoning_level'].value_counts()}")
    print(f"Turn types: {df_reasoning['turn_type'].value_counts()}")
    
    # Create the comprehensive analysis plots
    fig = create_asr_reasoning_plots(df_reasoning)
    
    # Save the plot
    output_path = '/home/dcruz/multi_turn_jailbreaks/asr_reasoning_analysis_replica.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Analysis saved to: {output_path}")
    
    # Save the processed data
    df_reasoning.to_csv('/home/dcruz/multi_turn_jailbreaks/reasoning_analysis_data.csv', index=False)
    print("Data saved to: reasoning_analysis_data.csv")
    
    # Print summary statistics
    print(f"\nSummary Statistics:")
    print(f"Total experiments: {len(df_reasoning)}")
    print(f"Multi-turn experiments: {len(df_reasoning[df_reasoning['turn_type'] == 'multi'])}")
    print(f"Average reasoning tokens per conversation: {df_reasoning['avg_reasoning_tokens'].mean():.1f}")
    print(f"Average max score: {df_reasoning['max_score'].mean():.3f}")
    print(f"Overall success rate: {((df_reasoning['max_score'] >= 0.5) | (df_reasoning['goal_achieved'])).mean() * 100:.1f}%")
    
    plt.show()

if __name__ == "__main__":
    main()