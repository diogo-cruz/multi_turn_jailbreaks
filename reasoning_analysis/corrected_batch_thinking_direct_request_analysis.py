#!/usr/bin/env python3
"""
Corrected Batch Thinking + Direct Request Analysis
Properly computes scores as maximum over rounds per JSONL file, then averages across test cases
Separates single-turn and multi-turn data
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    print("Filtering for batch_thinking data and direct_request tactic only")
    print("Computing max score per JSONL file, then averaging across test cases")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            # Collect data for this JSONL file (conversation)
            conversation_scores = []
            conversation_reasoning_tokens = []
            metadata = {}
            is_direct_request = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Check if this is direct_request tactic
                    jailbreak_tactic = data.get('jailbreak_tactic', '').lower()
                    if jailbreak_tactic == 'direct_request':
                        is_direct_request = True
                    
                    # Collect score from this round - treat scores not between 0 and 1 as 0
                    if data.get('score') is not None:
                        try:
                            score = float(data['score'])
                            if not (0 <= score <= 1):
                                score = 0
                            conversation_scores.append(score)
                        except (ValueError, TypeError):
                            conversation_scores.append(0)
                    
                    # Collect reasoning tokens from this round
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                        if reasoning_tokens > 0:
                            conversation_reasoning_tokens.append(reasoning_tokens)
                    
                    # Update metadata (should be same across all rounds)
                    if not metadata:
                        metadata = {
                            'model': data.get('target_model', 'unknown'),
                            'test_case': data.get('test_case', 'unknown'),
                            'jailbreak_tactic': data.get('jailbreak_tactic', 'unknown'),
                            'turn_type': data.get('turn_type', 'unknown'),
                            'reasoning_level': extract_reasoning_level(file_path.name, data)
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
                    'max_score': max_score,  # This is the key correction
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'total_reasoning_tokens': sum(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0,
                    'num_reasoning_rounds': len(conversation_reasoning_tokens),
                    'num_total_rounds': len(data_lines),
                    'num_scored_rounds': len(conversation_scores),
                    **metadata
                }
                
                # Separate by turn type
                if metadata.get('turn_type') == 'single_turn':
                    single_turn_data.append(conversation_record)
                elif metadata.get('turn_type') == 'multi_turn':
                    multi_turn_data.append(conversation_record)
                else:
                    # Infer from filename if turn_type is unknown
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

def analyze_data(df, turn_type):
    """Analyze the data for a specific turn type"""
    
    print(f"\n=== {turn_type.upper()} ANALYSIS ===")
    print(f"Total conversations: {len(df)}")
    print(f"Conversations with reasoning tokens > 0: {len(df[df['avg_reasoning_tokens'] > 0])}")
    
    if len(df) == 0:
        return None
    
    # Basic statistics
    print(f"\nMax Score Statistics:")
    print(f"Min: {df['max_score'].min():.3f}")
    print(f"Max: {df['max_score'].max():.3f}")
    print(f"Mean: {df['max_score'].mean():.3f}")
    print(f"Median: {df['max_score'].median():.3f}")
    
    print(f"\nReasoning Token Statistics:")
    print(f"Min: {df['avg_reasoning_tokens'].min():.0f}")
    print(f"Max: {df['avg_reasoning_tokens'].max():.0f}")
    print(f"Mean: {df['avg_reasoning_tokens'].mean():.0f}")
    print(f"Median: {df['avg_reasoning_tokens'].median():.0f}")
    
    # Success rate (max_score >= 1.0)
    success_rate = (df['max_score'] >= 1.0).mean() * 100
    print(f"Success Rate (max_score = 1.0): {success_rate:.2f}%")
    
    # Correlation analysis
    reasoning_score_corr = df['avg_reasoning_tokens'].corr(df['max_score'])
    print(f"Correlation (avg reasoning tokens vs max score): {reasoning_score_corr:.4f}")
    
    # Analysis by reasoning level
    print(f"\n=== BY REASONING LEVEL ===")
    for level in ['none', 'low', 'medium', 'high']:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens = level_data['avg_reasoning_tokens'].mean()
            avg_score = level_data['max_score'].mean()
            success_rate_level = (level_data['max_score'] >= 1.0).mean() * 100
            count = len(level_data)
            print(f"{level.title()}: avg_score={avg_score:.3f}, success_rate={success_rate_level:.1f}%, avg_tokens={avg_tokens:.0f}, n={count}")
    
    return {
        'reasoning_score_corr': reasoning_score_corr,
        'success_rate': success_rate,
        'mean_score': df['max_score'].mean()
    }

def create_reasoning_token_bins(df, turn_type):
    """Create reasoning token bins and analyze score distributions"""
    
    if len(df) == 0:
        return df, []
    
    print(f"\n=== {turn_type.upper()} REASONING TOKEN BINS ===")
    
    # Define bins
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Create bins
    df['reasoning_bin'] = pd.cut(df['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Print bin statistics
    for label in bin_labels:
        bin_data = df[df['reasoning_bin'] == label]
        if len(bin_data) > 0:
            avg_score = bin_data['max_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            count = len(bin_data)
            print(f"{label}: avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, n={count}")
    
    return df, bin_labels

def create_plots(single_df, multi_df, single_bins, multi_bins):
    """Create comprehensive plots for both single and multi-turn data"""
    
    print("\nGenerating comprehensive plots...")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 15))
    
    # Single-turn plots (top row)
    ax1 = plt.subplot(3, 4, 1)
    ax2 = plt.subplot(3, 4, 2)
    ax3 = plt.subplot(3, 4, 3)
    ax4 = plt.subplot(3, 4, 4)
    
    # Multi-turn plots (middle row)
    ax5 = plt.subplot(3, 4, 5)
    ax6 = plt.subplot(3, 4, 6)
    ax7 = plt.subplot(3, 4, 7)
    ax8 = plt.subplot(3, 4, 8)
    
    # Comparison plots (bottom row)
    ax9 = plt.subplot(3, 4, 9)
    ax10 = plt.subplot(3, 4, 10)
    ax11 = plt.subplot(3, 4, 11)
    ax12 = plt.subplot(3, 4, 12)
    
    # Single-turn analysis
    if len(single_df) > 0:
        # 1. Scatter plot: Reasoning tokens vs Max score
        ax1.scatter(single_df['avg_reasoning_tokens'], single_df['max_score'], alpha=0.6, s=30, color='blue')
        ax1.set_xlabel('Average Reasoning Tokens')
        ax1.set_ylabel('Maximum Score')
        ax1.set_title('Single-Turn: Reasoning Tokens vs Max Score')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # Add trend line
        if len(single_df) > 1:
            z = np.polyfit(single_df['avg_reasoning_tokens'], single_df['max_score'], 1)
            p = np.poly1d(z)
            ax1.plot(single_df['avg_reasoning_tokens'], p(single_df['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
        
        # 2. Score distribution by reasoning level
        reasoning_levels = ['none', 'low', 'medium', 'high']
        colors = ['red', 'orange', 'yellow', 'green']
        avg_scores = []
        level_counts = []
        
        for level in reasoning_levels:
            level_data = single_df[single_df['reasoning_level'] == level]
            if len(level_data) > 0:
                avg_scores.append(level_data['max_score'].mean())
                level_counts.append(len(level_data))
            else:
                avg_scores.append(0)
                level_counts.append(0)
        
        bars = ax2.bar(reasoning_levels, avg_scores, color=colors)
        ax2.set_ylabel('Average Maximum Score')
        ax2.set_title('Single-Turn: Avg Score by Reasoning Level')
        ax2.set_ylim(0, 1)
        
        # Add value labels
        for bar, value, count in zip(bars, avg_scores, level_counts):
            if count > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                        f'{value:.3f}\n(n={count})', ha='center', va='bottom', fontsize=9)
        
        # 3. Score distribution histogram
        ax3.hist(single_df['max_score'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_xlabel('Maximum Score')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Single-Turn: Score Distribution')
        ax3.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='Success (1.0)')
        ax3.legend()
        
        # 4. Score by reasoning token bins
        if len(single_bins) > 0:
            bin_scores = []
            bin_counts = []
            for label in single_bins:
                bin_data = single_df[single_df['reasoning_bin'] == label]
                if len(bin_data) > 0:
                    bin_scores.append(bin_data['max_score'].mean())
                    bin_counts.append(len(bin_data))
                else:
                    bin_scores.append(0)
                    bin_counts.append(0)
            
            bars = ax4.bar(single_bins, bin_scores, color='lightcoral', alpha=0.8)
            ax4.set_ylabel('Average Maximum Score')
            ax4.set_xlabel('Reasoning Token Bins')
            ax4.set_title('Single-Turn: Score by Token Bins')
            ax4.set_ylim(0, 1)
            plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels
            for bar, value, count in zip(bars, bin_scores, bin_counts):
                if count > 0:
                    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                            f'{value:.3f}\n(n={count})', ha='center', va='bottom', fontsize=8)
    
    # Multi-turn analysis (similar structure)
    if len(multi_df) > 0:
        # 5. Scatter plot: Reasoning tokens vs Max score
        ax5.scatter(multi_df['avg_reasoning_tokens'], multi_df['max_score'], alpha=0.6, s=30, color='green')
        ax5.set_xlabel('Average Reasoning Tokens')
        ax5.set_ylabel('Maximum Score')
        ax5.set_title('Multi-Turn: Reasoning Tokens vs Max Score')
        ax5.grid(True, alpha=0.3)
        ax5.set_ylim(0, 1)
        
        # Add trend line
        if len(multi_df) > 1:
            z = np.polyfit(multi_df['avg_reasoning_tokens'], multi_df['max_score'], 1)
            p = np.poly1d(z)
            ax5.plot(multi_df['avg_reasoning_tokens'], p(multi_df['avg_reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
        
        # 6. Score distribution by reasoning level
        avg_scores = []
        level_counts = []
        
        for level in reasoning_levels:
            level_data = multi_df[multi_df['reasoning_level'] == level]
            if len(level_data) > 0:
                avg_scores.append(level_data['max_score'].mean())
                level_counts.append(len(level_data))
            else:
                avg_scores.append(0)
                level_counts.append(0)
        
        bars = ax6.bar(reasoning_levels, avg_scores, color=colors)
        ax6.set_ylabel('Average Maximum Score')
        ax6.set_title('Multi-Turn: Avg Score by Reasoning Level')
        ax6.set_ylim(0, 1)
        
        # Add value labels
        for bar, value, count in zip(bars, avg_scores, level_counts):
            if count > 0:
                ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                        f'{value:.3f}\n(n={count})', ha='center', va='bottom', fontsize=9)
        
        # 7. Score distribution histogram
        ax7.hist(multi_df['max_score'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax7.set_xlabel('Maximum Score')
        ax7.set_ylabel('Frequency')
        ax7.set_title('Multi-Turn: Score Distribution')
        ax7.axvline(x=1.0, color='red', linestyle='--', alpha=0.7, label='Success (1.0)')
        ax7.legend()
        
        # 8. Score by reasoning token bins
        if len(multi_bins) > 0:
            bin_scores = []
            bin_counts = []
            for label in multi_bins:
                bin_data = multi_df[multi_df['reasoning_bin'] == label]
                if len(bin_data) > 0:
                    bin_scores.append(bin_data['max_score'].mean())
                    bin_counts.append(len(bin_data))
                else:
                    bin_scores.append(0)
                    bin_counts.append(0)
            
            bars = ax8.bar(multi_bins, bin_scores, color='mediumseagreen', alpha=0.8)
            ax8.set_ylabel('Average Maximum Score')
            ax8.set_xlabel('Reasoning Token Bins')
            ax8.set_title('Multi-Turn: Score by Token Bins')
            ax8.set_ylim(0, 1)
            plt.setp(ax8.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels
            for bar, value, count in zip(bars, bin_scores, bin_counts):
                if count > 0:
                    ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                            f'{value:.3f}\n(n={count})', ha='center', va='bottom', fontsize=8)
    
    # Comparison plots (bottom row)
    # 9. Overall score comparison
    if len(single_df) > 0 and len(multi_df) > 0:
        categories = ['Single-Turn', 'Multi-Turn']
        mean_scores = [single_df['max_score'].mean(), multi_df['max_score'].mean()]
        success_rates = [(single_df['max_score'] >= 1.0).mean() * 100, (multi_df['max_score'] >= 1.0).mean() * 100]
        
        bars = ax9.bar(categories, mean_scores, color=['blue', 'green'], alpha=0.7)
        ax9.set_ylabel('Average Maximum Score')
        ax9.set_title('Overall Score Comparison')
        ax9.set_ylim(0, 1)
        
        # Add value labels
        for bar, score, success in zip(bars, mean_scores, success_rates):
            ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{score:.3f}\n({success:.1f}% success)', ha='center', va='bottom')
    
    # 10. Sample size comparison
    if len(single_df) > 0 and len(multi_df) > 0:
        categories = ['Single-Turn', 'Multi-Turn']
        sample_sizes = [len(single_df), len(multi_df)]
        
        bars = ax10.bar(categories, sample_sizes, color=['blue', 'green'], alpha=0.7)
        ax10.set_ylabel('Number of Conversations')
        ax10.set_title('Sample Size Comparison')
        
        # Add value labels
        for bar, size in zip(bars, sample_sizes):
            ax10.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{size}', ha='center', va='bottom')
    
    # 11 & 12: Additional comparison plots can be added here
    ax11.text(0.5, 0.5, 'Additional\nComparison\nPlots', ha='center', va='center', transform=ax11.transAxes, fontsize=14)
    ax12.text(0.5, 0.5, 'Additional\nComparison\nPlots', ha='center', va='center', transform=ax12.transAxes, fontsize=14)
    
    plt.tight_layout()
    plt.savefig('corrected_batch_thinking_direct_request_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Corrected Batch Thinking + Direct Request Analysis...")
    print("- Computing max score per JSONL file")
    print("- Separating single-turn and multi-turn data")
    print("- Averaging scores across test cases")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Analyze single-turn data
    single_stats = analyze_data(single_df, "single-turn")
    single_df, single_bins = create_reasoning_token_bins(single_df, "single-turn")
    
    # Analyze multi-turn data  
    multi_stats = analyze_data(multi_df, "multi-turn")
    multi_df, multi_bins = create_reasoning_token_bins(multi_df, "multi-turn")
    
    # Create comprehensive plots
    create_plots(single_df, multi_df, single_bins, multi_bins)
    
    # Summary
    print("\n=== CORRECTED ANALYSIS SUMMARY ===")
    if single_stats:
        print(f"Single-Turn: avg_score={single_stats['mean_score']:.3f}, success_rate={single_stats['success_rate']:.1f}%, correlation={single_stats['reasoning_score_corr']:.4f}")
    if multi_stats:
        print(f"Multi-Turn: avg_score={multi_stats['mean_score']:.3f}, success_rate={multi_stats['success_rate']:.1f}%, correlation={multi_stats['reasoning_score_corr']:.4f}")
    
    print("\nCorrected analysis complete! Plot saved as 'corrected_batch_thinking_direct_request_analysis.png'")

if __name__ == "__main__":
    main()