#!/usr/bin/env python3
"""
Conversation-Level Reasoning Token Analysis
Analyzes the correlation between average reasoning token usage per conversation and jailbreak success rates
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

def load_conversation_level_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and aggregate by conversation (file)"""
    data_dir = Path(data_dir)
    all_conversations = []
    
    print("Loading conversation-level data from", data_dir)
    
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files (conversations)")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            # Aggregate data for this conversation
            conversation_reasoning_tokens = []
            final_success_score = None
            final_goal_achieved = None
            metadata = {}
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Collect reasoning tokens from each turn
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                        if reasoning_tokens > 0:  # Only count non-zero reasoning tokens
                            conversation_reasoning_tokens.append(reasoning_tokens)
                    
                    # Update metadata (should be same across all turns)
                    if not metadata:
                        metadata = {
                            'model': data.get('target_model', 'unknown'),
                            'test_case': data.get('test_case', 'unknown'),
                            'jailbreak_tactic': data.get('jailbreak_tactic', 'unknown'),
                            'turn_type': data.get('turn_type', 'unknown'),
                            'reasoning_level': extract_reasoning_level(file_path.name, data)
                        }
                    
                    # Keep updating success indicators (final one should be the conversation outcome)
                    if data.get('score') is not None:
                        final_success_score = data.get('score')
                    if data.get('goal_achieved') is not None:
                        final_goal_achieved = data.get('goal_achieved')
                        
                except json.JSONDecodeError as e:
                    print("JSON error in {}:{} - {}".format(file_path, line_num, e))
                    continue
                except Exception as e:
                    print("Error processing {}:{} - {}".format(file_path, line_num, e))
                    continue
            
            # Calculate conversation-level metrics
            avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
            total_reasoning_tokens = sum(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
            num_reasoning_turns = len(conversation_reasoning_tokens)
            
            conversation_record = {
                'file': file_path.name,
                'avg_reasoning_tokens': avg_reasoning_tokens,
                'total_reasoning_tokens': total_reasoning_tokens,
                'num_reasoning_turns': num_reasoning_turns,
                'num_total_turns': len(data_lines),
                'final_success_score': final_success_score,
                'final_goal_achieved': final_goal_achieved,
                **metadata
            }
            
            all_conversations.append(conversation_record)
                    
        except Exception as e:
            print("Error reading {}: {}".format(file_path, e))
            continue
    
    print("Loaded", len(all_conversations), "conversations")
    return pd.DataFrame(all_conversations)

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

def analyze_conversation_correlation(df):
    """Analyze correlation between average reasoning tokens and conversation success"""
    
    print("\n=== CONVERSATION-LEVEL REASONING ANALYSIS ===")
    print("Total conversations:", len(df))
    print("Conversations with reasoning tokens > 0:", len(df[df['avg_reasoning_tokens'] > 0]))
    
    # Basic statistics
    print("\nAverage Reasoning Tokens per Conversation:")
    print("Min:", df['avg_reasoning_tokens'].min())
    print("Max:", df['avg_reasoning_tokens'].max())
    print("Mean:", round(df['avg_reasoning_tokens'].mean(), 2))
    print("Median:", df['avg_reasoning_tokens'].median())
    
    # Success rate statistics
    df['success_score_numeric'] = pd.to_numeric(df['final_success_score'], errors='coerce')
    df['success'] = (df['success_score_numeric'] > 0.5) | (df['final_goal_achieved'] == True)
    overall_success_rate = df['success'].mean() * 100
    print("Overall Success Rate:", round(overall_success_rate, 2), "%")
    
    # Correlation analysis
    reasoning_success_corr = df['avg_reasoning_tokens'].corr(df['success'])
    reasoning_score_corr = df['avg_reasoning_tokens'].corr(df['success_score_numeric'])
    
    print("\nCorrelations:")
    print("Average Reasoning Tokens vs Success (binary):", round(reasoning_success_corr, 4))
    print("Average Reasoning Tokens vs Success Score:", round(reasoning_score_corr, 4))
    
    return {
        'reasoning_success_corr': reasoning_success_corr,
        'reasoning_score_corr': reasoning_score_corr,
        'overall_success_rate': overall_success_rate
    }

def analyze_by_reasoning_level(df):
    """Analyze success rates by reasoning level"""
    
    print("\n=== ANALYSIS BY REASONING LEVEL ===")
    
    for level in ['none', 'low', 'medium', 'high']:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens = level_data['avg_reasoning_tokens'].mean()
            success_rate = level_data['success'].mean() * 100
            count = len(level_data)
            avg_turns = level_data['num_total_turns'].mean()
            print("{}: {:.1f}% success rate (avg {:.0f} tokens/conv, {:.1f} avg turns, n={})".format(
                level.title(), success_rate, avg_tokens, avg_turns, count))

def create_conversation_visualization(df):
    """Create visualization for conversation-level analysis"""
    
    print("\nGenerating conversation-level visualization...")
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Scatter plot: Average reasoning tokens vs Success score
    ax1.scatter(df['avg_reasoning_tokens'], df['success_score_numeric'], alpha=0.6, s=30)
    ax1.set_xlabel('Average Reasoning Tokens per Conversation')
    ax1.set_ylabel('Final Success Score')
    ax1.set_title('Average Reasoning Tokens vs Conversation Success')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line if there's data
    valid_data = df.dropna(subset=['avg_reasoning_tokens', 'success_score_numeric'])
    if len(valid_data) > 1:
        z = np.polyfit(valid_data['avg_reasoning_tokens'], valid_data['success_score_numeric'], 1)
        p = np.poly1d(z)
        ax1.plot(valid_data['avg_reasoning_tokens'], p(valid_data['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
    
    # 2. Success rate by reasoning level
    reasoning_levels = ['none', 'low', 'medium', 'high']
    success_rates = []
    level_counts = []
    
    for level in reasoning_levels:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            success_rates.append(level_data['success'].mean() * 100)
            level_counts.append(len(level_data))
        else:
            success_rates.append(0)
            level_counts.append(0)
    
    bars = ax2.bar(reasoning_levels, success_rates, color=['red', 'orange', 'yellow', 'green'])
    ax2.set_ylabel('Success Rate (%)')
    ax2.set_title('Conversation Success Rate by Reasoning Level')
    ax2.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, value, count in zip(bars, success_rates, level_counts):
        if count > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    '{:.1f}%\n(n={})'.format(value, count), ha='center', va='bottom')
    
    # 3. Distribution of average reasoning tokens
    df_with_reasoning = df[df['avg_reasoning_tokens'] > 0]
    if len(df_with_reasoning) > 0:
        ax3.hist(df_with_reasoning['avg_reasoning_tokens'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_xlabel('Average Reasoning Tokens per Conversation')
        ax3.set_ylabel('Number of Conversations')
        ax3.set_title('Distribution of Average Reasoning Tokens\n(conversations with reasoning > 0)')
    
    # 4. Average reasoning tokens by level
    avg_tokens = []
    for level in reasoning_levels:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens.append(level_data['avg_reasoning_tokens'].mean())
        else:
            avg_tokens.append(0)
    
    bars = ax4.bar(reasoning_levels, avg_tokens, color=['red', 'orange', 'yellow', 'green'])
    ax4.set_ylabel('Average Reasoning Tokens per Conversation')
    ax4.set_title('Average Reasoning Tokens by Level')
    
    # Add value labels on bars
    for bar, value in zip(bars, avg_tokens):
        if value > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    '{:.0f}'.format(value), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('conversation_level_reasoning_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Conversation-Level Reasoning Token Analysis...")
    
    # Load data
    df = load_conversation_level_data()
    
    if len(df) == 0:
        print("No data found! Check if the batch_thinking directory exists and contains JSONL files.")
        return
    
    # Perform analyses
    correlations = analyze_conversation_correlation(df)
    analyze_by_reasoning_level(df)
    
    # Create visualization
    create_conversation_visualization(df)
    
    # Summary
    print("\n=== SUMMARY ===")
    print("Correlation between average reasoning tokens per conversation and success:")
    if correlations['reasoning_success_corr'] > 0.1:
        print("POSITIVE correlation - More reasoning tokens per conversation associated with higher success")
    elif correlations['reasoning_success_corr'] < -0.1:
        print("NEGATIVE correlation - More reasoning tokens per conversation associated with lower success")
    else:
        print("WEAK correlation - Limited relationship between reasoning tokens and success")
    
    print("\nConversation-level analysis complete! Visualization saved as 'conversation_level_reasoning_analysis.png'")

if __name__ == "__main__":
    main()