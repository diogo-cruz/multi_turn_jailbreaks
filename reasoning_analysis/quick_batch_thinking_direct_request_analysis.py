#!/usr/bin/env python3
"""
Quick Batch Thinking + Direct Request Analysis
Simple analysis without pandas dependency to avoid version conflicts
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

def load_and_analyze_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load and analyze data without pandas"""
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
                    
                    # Extract success indicators
                    success_score = data.get('score', 0)
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
                    
                    # Create record
                    record = {
                        'file': file_path.name,
                        'reasoning_tokens': reasoning_tokens,
                        'success_score': success_score,
                        'goal_achieved': goal_achieved,
                        'reasoning_level': reasoning_level,
                        'model': data.get('target_model', 'unknown'),
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
    return all_data

def analyze_data(data):
    """Analyze the loaded data"""
    
    # Convert success scores to numeric
    reasoning_tokens = []
    success_scores = []
    success_binary = []
    reasoning_levels = []
    
    for record in data:
        reasoning_tokens.append(record['reasoning_tokens'])
        
        # Handle success score - treat scores not between 0 and 1 as 0
        try:
            score = float(record['success_score'])
            if not (0 <= score <= 1):
                score = 0
            success_scores.append(score)
            success_binary.append(1 if score > 0.5 or record['goal_achieved'] else 0)
        except (ValueError, TypeError):
            success_scores.append(0)
            success_binary.append(1 if record['goal_achieved'] else 0)
        
        reasoning_levels.append(record['reasoning_level'])
    
    # Convert to numpy arrays
    reasoning_tokens = np.array(reasoning_tokens)
    success_scores = np.array(success_scores)
    success_binary = np.array(success_binary)
    
    print("\n=== ANALYSIS RESULTS ===")
    print(f"Total records: {len(data)}")
    print(f"Records with reasoning tokens > 0: {np.sum(reasoning_tokens > 0)}")
    print(f"Overall success rate: {np.mean(success_binary) * 100:.2f}%")
    
    # Correlation
    if len(reasoning_tokens) > 1:
        correlation = np.corrcoef(reasoning_tokens, success_binary)[0, 1]
        print(f"Correlation (reasoning tokens vs success): {correlation:.4f}")
    
    # Analysis by reasoning level
    print("\n=== BY REASONING LEVEL ===")
    level_stats = defaultdict(list)
    for i, level in enumerate(reasoning_levels):
        level_stats[level].append({
            'reasoning_tokens': reasoning_tokens[i],
            'success': success_binary[i]
        })
    
    for level in ['none', 'low', 'medium', 'high']:
        if level in level_stats:
            level_data = level_stats[level]
            avg_tokens = np.mean([d['reasoning_tokens'] for d in level_data])
            success_rate = np.mean([d['success'] for d in level_data]) * 100
            count = len(level_data)
            print(f"{level.title()}: {success_rate:.1f}% success rate (avg {avg_tokens:.0f} tokens, n={count})")
    
    return reasoning_tokens, success_scores, success_binary, reasoning_levels, level_stats

def create_plots(reasoning_tokens, success_scores, success_binary, reasoning_levels, level_stats):
    """Create visualization plots"""
    
    print("\nGenerating plots...")
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Scatter plot: Reasoning tokens vs Success score
    ax1.scatter(reasoning_tokens, success_scores, alpha=0.6, s=30)
    ax1.set_xlabel('Reasoning Tokens')
    ax1.set_ylabel('Success Score')
    ax1.set_title('Reasoning Tokens vs Success Score\n(Batch Thinking, Direct Request)')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line if there's enough data
    if len(reasoning_tokens) > 1:
        valid_mask = ~np.isnan(success_scores)
        if np.sum(valid_mask) > 1:
            z = np.polyfit(reasoning_tokens[valid_mask], success_scores[valid_mask], 1)
            p = np.poly1d(z)
            ax1.plot(reasoning_tokens, p(reasoning_tokens), "r--", alpha=0.8, linewidth=2)
    
    # 2. Success rate by reasoning level
    levels = ['none', 'low', 'medium', 'high']
    success_rates = []
    level_counts = []
    colors = ['red', 'orange', 'yellow', 'green']
    
    for level in levels:
        if level in level_stats:
            level_data = level_stats[level]
            success_rates.append(np.mean([d['success'] for d in level_data]) * 100)
            level_counts.append(len(level_data))
        else:
            success_rates.append(0)
            level_counts.append(0)
    
    bars = ax2.bar(levels, success_rates, color=colors)
    ax2.set_ylabel('Success Rate (%)')
    ax2.set_title('Success Rate by Reasoning Level\n(Batch Thinking, Direct Request)')
    ax2.set_ylim(0, 100)
    
    # Add value labels on bars
    for bar, value, count in zip(bars, success_rates, level_counts):
        if count > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{value:.1f}%\n(n={count})', ha='center', va='bottom')
    
    # 3. Distribution of reasoning tokens (excluding zeros)
    reasoning_nonzero = reasoning_tokens[reasoning_tokens > 0]
    if len(reasoning_nonzero) > 0:
        ax3.hist(reasoning_nonzero, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax3.set_xlabel('Reasoning Tokens')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Distribution of Reasoning Tokens\n(excluding zero tokens)')
    
    # 4. Average reasoning tokens by level
    avg_tokens = []
    for level in levels:
        if level in level_stats:
            level_data = level_stats[level]
            avg_tokens.append(np.mean([d['reasoning_tokens'] for d in level_data]))
        else:
            avg_tokens.append(0)
    
    bars = ax4.bar(levels, avg_tokens, color=colors)
    ax4.set_ylabel('Average Reasoning Tokens')
    ax4.set_title('Average Reasoning Tokens by Level\n(Batch Thinking, Direct Request)')
    
    # Add value labels on bars
    for bar, value in zip(bars, avg_tokens):
        if value > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{value:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('quick_batch_thinking_direct_request_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function"""
    print("Starting Quick Batch Thinking + Direct Request Analysis...")
    
    # Load data
    data = load_and_analyze_data()
    
    if len(data) == 0:
        print("No data found!")
        return
    
    # Analyze data
    reasoning_tokens, success_scores, success_binary, reasoning_levels, level_stats = analyze_data(data)
    
    # Create plots
    create_plots(reasoning_tokens, success_scores, success_binary, reasoning_levels, level_stats)
    
    print("\nAnalysis complete! Plot saved as 'quick_batch_thinking_direct_request_analysis.png'")

if __name__ == "__main__":
    main()