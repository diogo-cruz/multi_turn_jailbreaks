#!/usr/bin/env python3
"""
Multi-Turn Minimum Score Analysis - Batch Thinking + Direct Request
Analyzes the correlation between average reasoning tokens and minimum score achieved in multi-turn conversations
Filtered for batch_thinking data and direct_request tactic only
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_multiturn_min_score_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load multi-turn conversations and calculate minimum score vs average reasoning tokens"""
    data_dir = Path(data_dir)
    all_conversations = []
    
    print("Loading multi-turn conversation data from", data_dir)
    print("Filtering for batch_thinking data and direct_request tactic only")
    
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    multiturn_files = [f for f in jsonl_files if 'multi_turn' in f.name]
    print("Found", len(multiturn_files), "multi-turn JSONL files")
    
    for file_path in multiturn_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            # Collect data for this conversation
            conversation_reasoning_tokens = []
            conversation_scores = []
            metadata = {}
            is_direct_request = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Check if this is direct_request tactic
                    jailbreak_tactic = data.get('jailbreak_tactic', '').lower()
                    if jailbreak_tactic == 'direct_request':
                        is_direct_request = True
                    
                    # Collect reasoning tokens from each turn
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                        if reasoning_tokens > 0:  # Only count non-zero reasoning tokens
                            conversation_reasoning_tokens.append(reasoning_tokens)
                    
                    # Collect scores from each turn - treat scores not between 0 and 1 as 0
                    if data.get('score') is not None:
                        try:
                            score = float(data['score'])
                            if not (0 <= score <= 1):
                                score = 0
                            conversation_scores.append(score)
                        except (ValueError, TypeError):
                            pass  # Skip non-numeric scores
                    
                    # Update metadata (should be same across all turns)
                    if not metadata:
                        metadata = {
                            'model': data.get('target_model', 'unknown'),
                            'test_case': data.get('test_case', 'unknown'),
                            'jailbreak_tactic': data.get('jailbreak_tactic', 'unknown'),
                            'reasoning_level': extract_reasoning_level(file_path.name, data)
                        }
                        
                except json.JSONDecodeError as e:
                    print("JSON error in {}:{} - {}".format(file_path, line_num, e))
                    continue
                except Exception as e:
                    print("Error processing {}:{} - {}".format(file_path, line_num, e))
                    continue
            
            # Only include conversations with direct_request tactic and scores
            if is_direct_request and conversation_scores:
                avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
                min_score = min(conversation_scores)
                max_score = max(conversation_scores)
                num_turns_with_scores = len(conversation_scores)
                
                conversation_record = {
                    'file': file_path.name,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'total_reasoning_tokens': sum(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0,
                    'num_reasoning_turns': len(conversation_reasoning_tokens),
                    'min_score': min_score,
                    'max_score': max_score,
                    'num_turns_with_scores': num_turns_with_scores,
                    'num_total_turns': len(data_lines),
                    **metadata
                }
                
                all_conversations.append(conversation_record)
                    
        except Exception as e:
            print("Error reading {}: {}".format(file_path, e))
            continue
    
    df = pd.DataFrame(all_conversations)
    
    # Filter out negative scores and none reasoning cases
    print("Before filtering - Total conversations:", len(df))
    
    # Filter out negative minimum scores
    df = df[df['min_score'] >= 0]
    print("After filtering negative scores:", len(df))
    
    # Filter out 'none' reasoning level
    df = df[df['reasoning_level'] != 'none']
    print("After filtering 'none' reasoning level:", len(df))
    
    # Filter out outliers with average reasoning tokens > 10000
    df = df[df['avg_reasoning_tokens'] <= 10000]
    print("After filtering outliers (avg_reasoning_tokens > 10000):", len(df))
    
    print("Final dataset:", len(df), "multi-turn conversations with direct_request tactic")
    return df

def extract_reasoning_level(filename, data):
    """Extract reasoning level from filename or data"""
    if 'reasoning_high' in filename:
        return 'high'
    elif 'reasoning_medium' in filename:
        return 'medium'
    elif 'reasoning_low' in filename:
        return 'low'
    elif 'reasoning_none' in filename:
        return 'none'
    return 'unknown'

def analyze_min_score_correlation(df):
    """Analyze correlation between average reasoning tokens and minimum score"""
    
    print("\n=== MULTI-TURN MINIMUM SCORE ANALYSIS (BATCH_THINKING + DIRECT_REQUEST) ===")
    print("Total multi-turn conversations:", len(df))
    print("Conversations with reasoning tokens > 0:", len(df[df['avg_reasoning_tokens'] > 0]))
    
    # Basic statistics
    print("\nAverage Reasoning Tokens per Conversation:")
    print("Min:", round(df['avg_reasoning_tokens'].min(), 2))
    print("Max:", round(df['avg_reasoning_tokens'].max(), 2))
    print("Mean:", round(df['avg_reasoning_tokens'].mean(), 2))
    print("Median:", round(df['avg_reasoning_tokens'].median(), 2))
    
    print("\nMinimum Score Statistics:")
    print("Min:", round(df['min_score'].min(), 2))
    print("Max:", round(df['min_score'].max(), 2))
    print("Mean:", round(df['min_score'].mean(), 2))
    print("Median:", round(df['min_score'].median(), 2))
    
    # Correlation analysis
    reasoning_min_score_corr = df['avg_reasoning_tokens'].corr(df['min_score'])
    reasoning_max_score_corr = df['avg_reasoning_tokens'].corr(df['max_score'])
    
    print("\nCorrelations:")
    print("Average Reasoning Tokens vs Minimum Score:", round(reasoning_min_score_corr, 4))
    print("Average Reasoning Tokens vs Maximum Score:", round(reasoning_max_score_corr, 4))
    
    # Success rate analysis (max_score = 1.0 as success, indicating goal achieved)
    df['goal_success'] = df['max_score'] >= 1.0
    success_rate = df['goal_success'].mean() * 100
    print("Success Rate (max_score = 1.0, goal achieved):", round(success_rate, 2), "%")
    
    return {
        'reasoning_min_score_corr': reasoning_min_score_corr,
        'reasoning_max_score_corr': reasoning_max_score_corr,
        'success_rate': success_rate
    }

def analyze_by_reasoning_level(df):
    """Analyze minimum scores by reasoning level"""
    
    print("\n=== ANALYSIS BY REASONING LEVEL ===")
    
    for level in ['low', 'medium', 'high']:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens = level_data['avg_reasoning_tokens'].mean()
            avg_min_score = level_data['min_score'].mean()
            success_rate = (level_data['max_score'] >= 1.0).mean() * 100
            count = len(level_data)
            print("{}: avg min_score={:.3f}, success_rate={:.1f}%, avg_tokens={:.0f}, n={}".format(
                level.title(), avg_min_score, success_rate, avg_tokens, count))

def analyze_by_token_bins(df):
    """Analyze success rates by average reasoning token bins"""
    
    print("\n=== ANALYSIS BY TOKEN BINS ===")
    
    # Define token bins
    bins = [0, 500, 1000, 1500, 2000, 2500, float('inf')]
    labels = ['0-500', '500-1000', '1000-1500', '1500-2000', '2000-2500', '2500+']
    
    # Create token bins
    df['token_bin'] = pd.cut(df['avg_reasoning_tokens'], bins=bins, labels=labels, right=False)
    
    print("Success rate by average reasoning token bins:")
    for label in labels:
        bin_data = df[df['token_bin'] == label]
        if len(bin_data) > 0:
            avg_min_score = bin_data['min_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = bin_data['avg_reasoning_tokens'].mean()
            count = len(bin_data)
            print("{}: avg min_score={:.3f}, success_rate={:.1f}%, avg_tokens={:.0f}, n={}".format(
                label, avg_min_score, success_rate, avg_tokens, count))
        else:
            print("{}: No data".format(label))
    
    return df

def analyze_by_fixed_token_ranges(df):
    """Analyze success rates by fixed token ranges"""
    
    print("\n=== ANALYSIS BY FIXED TOKEN RANGES ===")
    
    # Define fixed token ranges
    ranges = [(0, 400), (400, 800), (800, 1200), (1200, 1600), (1600, float('inf'))]
    range_labels = ['0-400', '400-800', '800-1200', '1200-1600', '1600+']
    
    # Create range bins
    df['token_range_bin'] = -1
    df['token_range_label'] = ''
    
    for i, (min_val, max_val) in enumerate(ranges):
        if max_val == float('inf'):
            mask = df['avg_reasoning_tokens'] >= min_val
        else:
            mask = (df['avg_reasoning_tokens'] >= min_val) & (df['avg_reasoning_tokens'] < max_val)
        
        df.loc[mask, 'token_range_bin'] = i
        df.loc[mask, 'token_range_label'] = range_labels[i]
    
    print("Success rate by fixed token ranges:")
    for i, label in enumerate(range_labels):
        bin_data = df[df['token_range_bin'] == i]
        if len(bin_data) > 0:
            avg_min_score = bin_data['min_score'].mean()
            avg_max_score = bin_data['max_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = bin_data['avg_reasoning_tokens'].mean()
            count = len(bin_data)
            print(f"{label}: avg min_score={avg_min_score:.3f}, avg max_score={avg_max_score:.3f}, success_rate={success_rate:.1f}%, avg_tokens={avg_tokens:.0f}, n={count}")
        else:
            print(f"{label}: No data")
    
    return df, range_labels

def create_min_score_visualization(df, fixed_range_labels):
    """Create visualization for minimum score analysis"""
    
    print("\nGenerating minimum score visualization...")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 18))
    ax1 = plt.subplot(3, 2, 1)
    ax2 = plt.subplot(3, 2, 2)
    ax3 = plt.subplot(3, 2, 3)
    ax4 = plt.subplot(3, 2, 4)
    ax5 = plt.subplot(3, 2, 5)
    ax6 = plt.subplot(3, 2, 6)  # New plot for average reasoning tokens by max score
    
    # 1. Scatter plot: Average reasoning tokens vs Maximum score
    ax1.scatter(df['avg_reasoning_tokens'], df['max_score'], alpha=0.6, s=30)
    ax1.set_xlabel('Average Reasoning Tokens per Conversation')
    ax1.set_ylabel('Maximum Score in Conversation')
    ax1.set_title('Average Reasoning Tokens vs Maximum Score\n(Multi-Turn, Batch Thinking, Direct Request)')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    if len(df) > 1:
        z = np.polyfit(df['avg_reasoning_tokens'], df['max_score'], 1)
        p = np.poly1d(z)
        ax1.plot(df['avg_reasoning_tokens'], p(df['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
    
    # 2. Average maximum score by reasoning level
    reasoning_levels = ['low', 'medium', 'high']
    avg_max_scores = []
    level_counts = []
    
    for level in reasoning_levels:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_max_scores.append(level_data['max_score'].mean())
            level_counts.append(len(level_data))
        else:
            avg_max_scores.append(0)
            level_counts.append(0)
    
    bars = ax2.bar(reasoning_levels, avg_max_scores, color=['orange', 'yellow', 'green'])
    ax2.set_ylabel('Average Maximum Score')
    ax2.set_title('Average Maximum Score by Reasoning Level\n(Multi-Turn, Batch Thinking, Direct Request)')
    ax2.set_ylim(0, 1)
    
    # Add value labels on bars
    for bar, value, count in zip(bars, avg_max_scores, level_counts):
        if count > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    '{:.3f}\n(n={})'.format(value, count), ha='center', va='bottom')
    
    # 3. Distribution of maximum scores
    ax3.hist(df['max_score'], bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
    ax3.set_xlabel('Maximum Score')
    ax3.set_ylabel('Number of Conversations')
    ax3.set_title('Distribution of Maximum Scores\n(Multi-Turn, Batch Thinking, Direct Request)')
    ax3.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='Goal Achieved (1.0)')
    ax3.legend()
    
    # 4. Success rate by reasoning level
    success_rates = []
    for level in reasoning_levels:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            success_rates.append((level_data['max_score'] >= 1.0).mean() * 100)
        else:
            success_rates.append(0)
    
    bars = ax4.bar(reasoning_levels, success_rates, color=['orange', 'yellow', 'green'])
    ax4.set_ylabel('Success Rate (%)')
    ax4.set_title('Success Rate by Reasoning Level\n(Multi-Turn, Batch Thinking, Direct Request)\n(max_score = 1.0, goal achieved)')
    ax4.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, value, count in zip(bars, success_rates, level_counts):
        if count > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    '{:.1f}%'.format(value), ha='center', va='bottom')
    
    # 5. Success rate and average max score by fixed token ranges (dual y-axis)
    range_success_rates = []
    range_avg_max_scores = []
    range_counts = []
    
    for i, label in enumerate(fixed_range_labels):
        bin_data = df[df['token_range_bin'] == i]
        if len(bin_data) > 0:
            range_success_rates.append((bin_data['max_score'] >= 1.0).mean() * 100)
            range_avg_max_scores.append(bin_data['max_score'].mean())
            range_counts.append(len(bin_data))
        else:
            range_success_rates.append(0)
            range_avg_max_scores.append(0)
            range_counts.append(0)
    
    # Create dual y-axis
    ax5_twin = ax5.twinx()
    
    # Plot success rate as bars
    bars1 = ax5.bar(fixed_range_labels, range_success_rates, color='lightcoral', alpha=0.7, width=0.6, label='Success Rate (%)')
    ax5.set_ylabel('Success Rate (%)', color='red')
    ax5.tick_params(axis='y', labelcolor='red')
    
    # Plot average max score as line
    line1 = ax5_twin.plot(fixed_range_labels, range_avg_max_scores, color='blue', marker='o', linewidth=3, markersize=8, label='Avg Max Score')
    ax5_twin.set_ylabel('Average Maximum Score', color='blue')
    ax5_twin.tick_params(axis='y', labelcolor='blue')
    ax5_twin.set_ylim(0, 1)
    
    ax5.set_xlabel('Average Reasoning Tokens per Conversation')
    ax5.set_title('Success Rate & Avg Max Score by Token Ranges\n(Multi-Turn, Batch Thinking, Direct Request)')
    ax5.set_ylim(0, max(range_success_rates) * 1.2 if range_success_rates else 100)
    plt.setp(ax5.get_xticklabels(), rotation=45, ha='right')
    
    # Add value labels for success rate bars
    for bar, value, count in zip(bars1, range_success_rates, range_counts):
        if count > 0:
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    '{:.1f}%\n(n={})'.format(value, count), ha='center', va='bottom', color='red', fontsize=9)
    
    # Add value labels for average max score line
    for i, (label, avg_score) in enumerate(zip(fixed_range_labels, range_avg_max_scores)):
        if range_counts[i] > 0:
            ax5_twin.text(i, avg_score + 0.05, '{:.3f}'.format(avg_score), ha='center', va='bottom', color='blue', fontsize=9)
    
    # Add legends
    ax5.legend(loc='upper left')
    ax5_twin.legend(loc='upper right')
    
    # 6. Average reasoning tokens by maximum score bins
    # Create max score bins
    max_score_bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    max_score_labels = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0']
    
    avg_reasoning_by_max_score = []
    max_score_counts = []
    
    for i in range(len(max_score_bins)-1):
        min_score = max_score_bins[i]
        max_score = max_score_bins[i+1]
        
        if i == len(max_score_bins)-2:  # Last bin, include upper bound
            bin_data = df[(df['max_score'] >= min_score) & (df['max_score'] <= max_score)]
        else:
            bin_data = df[(df['max_score'] >= min_score) & (df['max_score'] < max_score)]
        
        if len(bin_data) > 0:
            avg_reasoning_by_max_score.append(bin_data['avg_reasoning_tokens'].mean())
            max_score_counts.append(len(bin_data))
        else:
            avg_reasoning_by_max_score.append(0)
            max_score_counts.append(0)
    
    bars = ax6.bar(max_score_labels, avg_reasoning_by_max_score, color='mediumseagreen', alpha=0.8)
    ax6.set_ylabel('Average Reasoning Tokens')
    ax6.set_xlabel('Maximum Score Bins')
    ax6.set_title('Average Reasoning Tokens by Maximum Score Bins\n(Multi-Turn, Batch Thinking, Direct Request)')
    plt.setp(ax6.get_xticklabels(), rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, value, count in zip(bars, avg_reasoning_by_max_score, max_score_counts):
        if count > 0:
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                    '{:.0f}\n(n={})'.format(value, count), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('batch_thinking_direct_request_multiturn_min_score_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Multi-Turn Minimum Score Analysis for Batch Thinking + Direct Request...")
    
    # Load data
    df = load_multiturn_min_score_data()
    
    if len(df) == 0:
        print("No multi-turn data found for batch_thinking + direct_request!")
        return
    
    # Perform analyses
    correlations = analyze_min_score_correlation(df)
    analyze_by_reasoning_level(df)
    df = analyze_by_token_bins(df)
    df, fixed_range_labels = analyze_by_fixed_token_ranges(df)
    
    # Create visualization
    create_min_score_visualization(df, fixed_range_labels)
    
    # Summary
    print("\n=== SUMMARY ===")
    print("Correlation between average reasoning tokens and minimum score in multi-turn conversations (batch_thinking + direct_request):")
    if correlations['reasoning_min_score_corr'] > 0.1:
        print("POSITIVE correlation - More reasoning tokens associated with higher minimum scores")
    elif correlations['reasoning_min_score_corr'] < -0.1:
        print("NEGATIVE correlation - More reasoning tokens associated with lower minimum scores")
    else:
        print("WEAK correlation - Limited relationship between reasoning tokens and minimum scores")
    
    print("\nMulti-turn minimum score analysis complete! Visualization saved as 'batch_thinking_direct_request_multiturn_min_score_analysis.png'")

if __name__ == "__main__":
    main()