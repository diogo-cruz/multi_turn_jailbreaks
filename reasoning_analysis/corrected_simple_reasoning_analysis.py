#!/usr/bin/env python3
"""
Corrected Simple Reasoning Token Analysis - Batch Thinking + Direct Request
Analyzes the correlation between reasoning token usage and jailbreak success rates
Properly computes scores as maximum over rounds per JSONL file
Separates single-turn and multi-turn data
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    print("Filtering for batch_thinking data and direct_request tactic only")
    print("Computing max score per JSONL file correctly")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            # Collect data for this JSONL file
            conversation_scores = []
            conversation_reasoning_tokens = []
            metadata = {}
            is_direct_request = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Filter for direct_request tactic only
                    jailbreak_tactic = data.get('jailbreak_tactic', '').lower()
                    if jailbreak_tactic == 'direct_request':
                        is_direct_request = True
                    
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
                    
                    # Extract other metadata
                    if not metadata:
                        metadata = {
                            'model': data.get('target_model', 'unknown'),
                            'test_case': data.get('test_case', 'unknown'),
                            'turn_type': data.get('turn_type', 'unknown'),
                            'reasoning_level': extract_reasoning_level(file_path.name, data),
                            'goal_achieved': data.get('goal_achieved', False),
                            'rejected': data.get('rejected', False)
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
            # Only include conversations with direct_request tactic and scores
            if is_direct_request and conversation_scores:
                # CORRECT SCORE COMPUTATION: Maximum score across all rounds
                max_score = max(conversation_scores)
                
                # Average reasoning tokens (only counting non-zero tokens)
                avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
                
                conversation_record = {
                    'file': file_path.name,
                    'max_score': max_score,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'num_rounds': len(conversation_scores),
                    **metadata
                }
                
                # Separate by turn type
                if metadata.get('turn_type') == 'single_turn':
                    single_turn_data.append(conversation_record)
                elif metadata.get('turn_type') == 'multi_turn':
                    multi_turn_data.append(conversation_record)
                else:
                    # Infer from filename
                    if 'single_turn' in file_path.name:
                        single_turn_data.append(conversation_record)
                    elif 'multi_turn' in file_path.name:
                        multi_turn_data.append(conversation_record)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(single_turn_data)} single-turn conversations")
    print(f"Loaded {len(multi_turn_data)} multi-turn conversations")
    
    return pd.DataFrame(single_turn_data), pd.DataFrame(multi_turn_data)

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

def analyze_reasoning_correlation(df, turn_type):
    """Analyze correlation between reasoning tokens and success"""
    
    print(f"\n=== {turn_type.upper()} REASONING TOKEN ANALYSIS ===")
    print(f"Total conversations: {len(df)}")
    
    if len(df) == 0:
        print("No data available")
        return None
    
    print(f"Conversations with reasoning tokens > 0: {len(df[df['avg_reasoning_tokens'] > 0])}")
    
    # Basic statistics
    print(f"\nReasoning Token Statistics:")
    print(f"Min: {df['avg_reasoning_tokens'].min():.0f}")
    print(f"Max: {df['avg_reasoning_tokens'].max():.0f}")
    print(f"Mean: {df['avg_reasoning_tokens'].mean():.2f}")
    print(f"Median: {df['avg_reasoning_tokens'].median():.2f}")
    
    # Success rate statistics
    df['success'] = df['max_score'] >= 1.0
    overall_success_rate = df['success'].mean() * 100
    print(f"Overall Success Rate: {overall_success_rate:.2f}%")
    
    print(f"\nMax Score Statistics:")
    print(f"Min: {df['max_score'].min():.3f}")
    print(f"Max: {df['max_score'].max():.3f}")
    print(f"Mean: {df['max_score'].mean():.3f}")
    print(f"Median: {df['max_score'].median():.3f}")
    
    # Correlation analysis
    reasoning_success_corr = df['avg_reasoning_tokens'].corr(df['success'])
    reasoning_score_corr = df['avg_reasoning_tokens'].corr(df['max_score'])
    
    print(f"\nCorrelations:")
    print(f"Reasoning Tokens vs Success (binary): {reasoning_success_corr:.4f}")
    print(f"Reasoning Tokens vs Max Score: {reasoning_score_corr:.4f}")
    
    return {
        'reasoning_success_corr': reasoning_success_corr,
        'reasoning_score_corr': reasoning_score_corr,
        'overall_success_rate': overall_success_rate,
        'mean_score': df['max_score'].mean()
    }

def analyze_by_reasoning_level(df, turn_type):
    """Analyze success rates by reasoning level"""
    
    print(f"\n=== {turn_type.upper()} ANALYSIS BY REASONING LEVEL ===")
    
    if len(df) == 0:
        print("No data available")
        return
    
    for level in ['none', 'low', 'medium', 'high']:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens = level_data['avg_reasoning_tokens'].mean()
            avg_score = level_data['max_score'].mean()
            success_rate = level_data['success'].mean() * 100
            count = len(level_data)
            print(f"{level.title()}: avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, avg_tokens={avg_tokens:.0f}, n={count}")

def create_visualization(single_df, multi_df):
    """Create comprehensive visualization for both turn types"""
    
    print("\nGenerating corrected visualization...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 4, figsize=(20, 12))
    
    # Single-turn plots (top row)
    if len(single_df) > 0:
        # 1. Scatter plot: Reasoning tokens vs Max score
        axes[0, 0].scatter(single_df['avg_reasoning_tokens'], single_df['max_score'], alpha=0.6, s=30, color='blue')
        axes[0, 0].set_xlabel('Average Reasoning Tokens')
        axes[0, 0].set_ylabel('Maximum Score')
        axes[0, 0].set_title('Single-Turn: Reasoning Tokens vs Max Score')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1)
        
        # Add trend line
        if len(single_df) > 1:
            z = np.polyfit(single_df['avg_reasoning_tokens'], single_df['max_score'], 1)
            p = np.poly1d(z)
            axes[0, 0].plot(single_df['avg_reasoning_tokens'], p(single_df['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
        
        # 2. Success rate by reasoning level
        reasoning_levels = ['none', 'low', 'medium', 'high']
        colors = ['red', 'orange', 'yellow', 'green']
        success_rates = []
        level_counts = []
        
        for level in reasoning_levels:
            level_data = single_df[single_df['reasoning_level'] == level]
            if len(level_data) > 0:
                success_rates.append(level_data['success'].mean() * 100)
                level_counts.append(len(level_data))
            else:
                success_rates.append(0)
                level_counts.append(0)
        
        bars = axes[0, 1].bar(reasoning_levels, success_rates, color=colors)
        axes[0, 1].set_ylabel('Success Rate (%)')
        axes[0, 1].set_title('Single-Turn: Success Rate by Reasoning Level')
        axes[0, 1].set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, value, count in zip(bars, success_rates, level_counts):
            if count > 0:
                axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                        f'{value:.1f}%\n(n={count})', ha='center', va='bottom', fontsize=9)
        
        # 3. Distribution of reasoning tokens (excluding zeros)
        reasoning_nonzero = single_df[single_df['avg_reasoning_tokens'] > 0]['avg_reasoning_tokens']
        if len(reasoning_nonzero) > 0:
            axes[0, 2].hist(reasoning_nonzero, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 2].set_xlabel('Average Reasoning Tokens')
            axes[0, 2].set_ylabel('Frequency')
            axes[0, 2].set_title('Single-Turn: Distribution of Reasoning Tokens\n(excluding zero tokens)')
        
        # 4. Average reasoning tokens by level
        avg_tokens = []
        for level in reasoning_levels:
            level_data = single_df[single_df['reasoning_level'] == level]
            if len(level_data) > 0:
                avg_tokens.append(level_data['avg_reasoning_tokens'].mean())
            else:
                avg_tokens.append(0)
        
        bars = axes[0, 3].bar(reasoning_levels, avg_tokens, color=colors)
        axes[0, 3].set_ylabel('Average Reasoning Tokens')
        axes[0, 3].set_title('Single-Turn: Average Reasoning Tokens by Level')
        
        # Add value labels on bars
        for bar, value in zip(bars, avg_tokens):
            if value > 0:
                axes[0, 3].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                        f'{value:.0f}', ha='center', va='bottom', fontsize=9)
    else:
        for i in range(4):
            axes[0, i].text(0.5, 0.5, 'No Single-Turn Data', ha='center', va='center', transform=axes[0, i].transAxes)
    
    # Multi-turn plots (bottom row)
    if len(multi_df) > 0:
        # 5. Scatter plot: Reasoning tokens vs Max score
        axes[1, 0].scatter(multi_df['avg_reasoning_tokens'], multi_df['max_score'], alpha=0.6, s=30, color='green')
        axes[1, 0].set_xlabel('Average Reasoning Tokens')
        axes[1, 0].set_ylabel('Maximum Score')
        axes[1, 0].set_title('Multi-Turn: Reasoning Tokens vs Max Score')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 1)
        
        # Add trend line
        if len(multi_df) > 1:
            z = np.polyfit(multi_df['avg_reasoning_tokens'], multi_df['max_score'], 1)
            p = np.poly1d(z)
            axes[1, 0].plot(multi_df['avg_reasoning_tokens'], p(multi_df['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
        
        # 6. Success rate by reasoning level
        success_rates = []
        level_counts = []
        
        for level in reasoning_levels:
            level_data = multi_df[multi_df['reasoning_level'] == level]
            if len(level_data) > 0:
                success_rates.append(level_data['success'].mean() * 100)
                level_counts.append(len(level_data))
            else:
                success_rates.append(0)
                level_counts.append(0)
        
        bars = axes[1, 1].bar(reasoning_levels, success_rates, color=colors)
        axes[1, 1].set_ylabel('Success Rate (%)')
        axes[1, 1].set_title('Multi-Turn: Success Rate by Reasoning Level')
        axes[1, 1].set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, value, count in zip(bars, success_rates, level_counts):
            if count > 0:
                axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                        f'{value:.1f}%\n(n={count})', ha='center', va='bottom', fontsize=9)
        
        # 7. Distribution of reasoning tokens (excluding zeros)
        reasoning_nonzero = multi_df[multi_df['avg_reasoning_tokens'] > 0]['avg_reasoning_tokens']
        if len(reasoning_nonzero) > 0:
            axes[1, 2].hist(reasoning_nonzero, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            axes[1, 2].set_xlabel('Average Reasoning Tokens')
            axes[1, 2].set_ylabel('Frequency')
            axes[1, 2].set_title('Multi-Turn: Distribution of Reasoning Tokens\n(excluding zero tokens)')
        
        # 8. Average reasoning tokens by level
        avg_tokens = []
        for level in reasoning_levels:
            level_data = multi_df[multi_df['reasoning_level'] == level]
            if len(level_data) > 0:
                avg_tokens.append(level_data['avg_reasoning_tokens'].mean())
            else:
                avg_tokens.append(0)
        
        bars = axes[1, 3].bar(reasoning_levels, avg_tokens, color=colors)
        axes[1, 3].set_ylabel('Average Reasoning Tokens')
        axes[1, 3].set_title('Multi-Turn: Average Reasoning Tokens by Level')
        
        # Add value labels on bars
        for bar, value in zip(bars, avg_tokens):
            if value > 0:
                axes[1, 3].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10, 
                        f'{value:.0f}', ha='center', va='bottom', fontsize=9)
    else:
        for i in range(4):
            axes[1, i].text(0.5, 0.5, 'No Multi-Turn Data', ha='center', va='center', transform=axes[1, i].transAxes)
    
    plt.tight_layout()
    plt.savefig('corrected_simple_reasoning_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Corrected Simple Reasoning Token Analysis...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Perform analyses
    single_stats = analyze_reasoning_correlation(single_df, "single-turn")
    analyze_by_reasoning_level(single_df, "single-turn")
    
    multi_stats = analyze_reasoning_correlation(multi_df, "multi-turn")
    analyze_by_reasoning_level(multi_df, "multi-turn")
    
    # Create visualization
    create_visualization(single_df, multi_df)
    
    # Summary
    print("\n=== CORRECTED ANALYSIS SUMMARY ===")
    if single_stats:
        print(f"Single-Turn: correlation={single_stats['reasoning_score_corr']:.4f}, "
              f"avg_score={single_stats['mean_score']:.3f}, success_rate={single_stats['overall_success_rate']:.1f}%")
    if multi_stats:
        print(f"Multi-Turn: correlation={multi_stats['reasoning_score_corr']:.4f}, "
              f"avg_score={multi_stats['mean_score']:.3f}, success_rate={multi_stats['overall_success_rate']:.1f}%")
    
    print("\nCorrected analysis complete! Visualization saved as 'corrected_simple_reasoning_analysis.png'")

if __name__ == "__main__":
    main()