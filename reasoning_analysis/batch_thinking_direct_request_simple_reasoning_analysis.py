#!/usr/bin/env python3
"""
Simple Reasoning Token Analysis - Batch Thinking + Direct Request
Analyzes the correlation between reasoning token usage and jailbreak success rates
Filtered for batch_thinking data and direct_request tactic only
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import glob

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
                    
                    # Extract reasoning tokens from target_response
                    reasoning_tokens = 0
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                    
                    # Extract success indicators
                    success_score = data.get('score', 0)
                    goal_achieved = data.get('goal_achieved', False)
                    
                    # Extract reasoning level from filename or data
                    reasoning_level = extract_reasoning_level(file_path.name, data)
                    
                    # Extract other metadata
                    record = {
                        'file': file_path.name,
                        'reasoning_tokens': reasoning_tokens,
                        'success_score': success_score,
                        'goal_achieved': goal_achieved,
                        'reasoning_level': reasoning_level,
                        'model': data.get('target_model', 'unknown'),
                        'test_case': data.get('test_case', 'unknown'),
                        'jailbreak_tactic': data.get('jailbreak_tactic', 'unknown'),
                        'turn_type': data.get('turn_type', 'unknown'),
                        'round': data.get('round', 1),
                        'prompt_tokens': data.get('token_usage', {}).get('prompt_tokens', 0),
                        'completion_tokens': data.get('token_usage', {}).get('completion_tokens', 0),
                        'total_tokens': data.get('token_usage', {}).get('total_tokens', 0),
                        'rejected': data.get('rejected', False)
                    }
                    
                    all_data.append(record)
                    
                except json.JSONDecodeError as e:
                    print("JSON error in {}:{} - {}".format(file_path, line_num, e))
                    continue
                except Exception as e:
                    print("Error processing {}:{} - {}".format(file_path, line_num, e))
                    continue
                    
        except Exception as e:
            print("Error reading {}: {}".format(file_path, e))
            continue
    
    print("Loaded", len(all_data), "records with direct_request tactic")
    return pd.DataFrame(all_data)

def extract_reasoning_level(filename, data):
    """Extract reasoning level from filename or data"""
    
    # Check filename for reasoning level patterns
    if 'reasoning_high' in filename:
        return 'high'
    elif 'reasoning_medium' in filename:
        return 'medium'
    elif 'reasoning_low' in filename:
        return 'low'
    elif 'reasoning_none' in filename:
        return 'none'
    
    # Check data for reasoning field
    if 'reasoning' in data:
        return str(data['reasoning']).lower()
    
    # Default based on presence of reasoning tokens
    reasoning_tokens = 0
    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
        reasoning_tokens = data['token_usage']['reasoning_tokens']
    
    if reasoning_tokens > 0:
        return 'high'
    else:
        return 'none'

def analyze_reasoning_correlation(df):
    """Analyze correlation between reasoning tokens and success"""
    
    print("\n=== REASONING TOKEN ANALYSIS (BATCH_THINKING + DIRECT_REQUEST) ===")
    print("Total records:", len(df))
    print("Records with reasoning tokens > 0:", len(df[df['reasoning_tokens'] > 0]))
    
    # Basic statistics
    print("\nReasoning Token Statistics:")
    print("Min:", df['reasoning_tokens'].min())
    print("Max:", df['reasoning_tokens'].max())
    print("Mean:", round(df['reasoning_tokens'].mean(), 2))
    print("Median:", df['reasoning_tokens'].median())
    
    # Success rate statistics
    # Handle mixed data types in success_score and treat scores not between 0 and 1 as 0
    df['success_score_numeric'] = pd.to_numeric(df['success_score'], errors='coerce')
    df['success_score_numeric'] = df['success_score_numeric'].apply(lambda x: x if (0 <= x <= 1) else 0 if pd.notna(x) else 0)
    df['success'] = (df['success_score_numeric'] > 0.5) | (df['goal_achieved'] == True)
    overall_success_rate = df['success'].mean() * 100
    print("Overall Success Rate:", round(overall_success_rate, 2), "%")
    
    # Correlation analysis
    reasoning_success_corr = df['reasoning_tokens'].corr(df['success'])
    reasoning_score_corr = df['reasoning_tokens'].corr(df['success_score_numeric'])
    
    print("\nCorrelations:")
    print("Reasoning Tokens vs Success (binary):", round(reasoning_success_corr, 4))
    print("Reasoning Tokens vs Success Score:", round(reasoning_score_corr, 4))
    
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
            avg_tokens = level_data['reasoning_tokens'].mean()
            success_rate = level_data['success'].mean() * 100
            count = len(level_data)
            print("{}: {:.1f}% success rate (avg {:.0f} tokens, n={})".format(
                level.title(), success_rate, avg_tokens, count))

def analyze_by_model(df):
    """Analyze success rates by model"""
    
    print("\n=== ANALYSIS BY MODEL ===")
    
    for model in df['model'].unique():
        model_data = df[df['model'] == model]
        if len(model_data) > 5:  # Only show models with sufficient data
            avg_tokens = model_data['reasoning_tokens'].mean()
            success_rate = model_data['success'].mean() * 100
            count = len(model_data)
            print("{}: {:.1f}% success rate (avg {:.0f} tokens, n={})".format(
                model, success_rate, avg_tokens, count))

def create_simple_visualization(df):
    """Create a simple visualization"""
    
    print("\nGenerating visualization...")
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Scatter plot: Reasoning tokens vs Success score
    ax1.scatter(df['reasoning_tokens'], df['success_score_numeric'], alpha=0.6, s=30)
    ax1.set_xlabel('Reasoning Tokens')
    ax1.set_ylabel('Success Score')
    ax1.set_title('Reasoning Tokens vs Success Score\n(Batch Thinking, Direct Request)')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line if there's data
    if len(df[df['reasoning_tokens'] > 0]) > 1:
        # Filter out NaN values for trend line
        valid_data = df.dropna(subset=['reasoning_tokens', 'success_score_numeric'])
        if len(valid_data) > 1:
            z = np.polyfit(valid_data['reasoning_tokens'], valid_data['success_score_numeric'], 1)
            p = np.poly1d(z)
            ax1.plot(valid_data['reasoning_tokens'], p(valid_data['reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
    
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
    ax2.set_title('Success Rate by Reasoning Level\n(Batch Thinking, Direct Request)')
    ax2.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, value, count in zip(bars, success_rates, level_counts):
        if count > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    '{:.1f}%\n(n={})'.format(value, count), ha='center', va='bottom')
    
    # 3. Distribution of reasoning tokens
    df_with_reasoning = df[df['reasoning_tokens'] > 0]
    if len(df_with_reasoning) > 0:
        ax3.hist(df_with_reasoning['reasoning_tokens'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_xlabel('Reasoning Tokens')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Distribution of Reasoning Tokens\n(excluding zero tokens, Batch Thinking, Direct Request)')
    
    # 4. Average reasoning tokens by level
    avg_tokens = []
    for level in reasoning_levels:
        level_data = df[df['reasoning_level'] == level]
        if len(level_data) > 0:
            avg_tokens.append(level_data['reasoning_tokens'].mean())
        else:
            avg_tokens.append(0)
    
    bars = ax4.bar(reasoning_levels, avg_tokens, color=['red', 'orange', 'yellow', 'green'])
    ax4.set_ylabel('Average Reasoning Tokens')
    ax4.set_title('Average Reasoning Tokens by Level\n(Batch Thinking, Direct Request)')
    
    # Add value labels on bars
    for bar, value in zip(bars, avg_tokens):
        if value > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    '{:.0f}'.format(value), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('batch_thinking_direct_request_reasoning_token_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Reasoning Token Analysis for Batch Thinking + Direct Request...")
    
    # Load data
    df = load_batch_thinking_data()
    
    if len(df) == 0:
        print("No data found for batch_thinking + direct_request! Check if the batch_thinking directory exists and contains JSONL files with direct_request tactic.")
        return
    
    # Perform analyses
    correlations = analyze_reasoning_correlation(df)
    analyze_by_reasoning_level(df)
    analyze_by_model(df)
    
    # Create visualization
    create_simple_visualization(df)
    
    # Summary
    print("\n=== SUMMARY ===")
    print("Correlation between reasoning tokens and success (batch_thinking + direct_request):")
    if correlations['reasoning_success_corr'] > 0.1:
        print("POSITIVE correlation - More reasoning tokens associated with higher success")
    elif correlations['reasoning_success_corr'] < -0.1:
        print("NEGATIVE correlation - More reasoning tokens associated with lower success")
    else:
        print("WEAK correlation - Limited relationship between reasoning tokens and success")
    
    print("\nAnalysis complete! Visualization saved as 'batch_thinking_direct_request_reasoning_token_analysis.png'")

if __name__ == "__main__":
    main()