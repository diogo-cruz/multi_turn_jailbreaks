#!/usr/bin/env python3
"""
Corrected Test Case Comparison Analysis - Batch Thinking + Direct Request
Plots score vs reasoning tokens (in bins) for single and multi-turn, separately for each test case
Properly computes scores as maximum over rounds per JSONL file
Groups by test case instead of model, averaging results over models
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import math

def clean_model_name(raw_model_name):
    """Clean up model names for display"""
    if not raw_model_name or raw_model_name == 'unknown':
        return 'unknown'
    
    # Remove provider prefixes and extract main model name
    model_name = raw_model_name.lower()
    
    if 'claude' in model_name:
        return 'Claude'
    elif 'gemini' in model_name:
        return None  # Exclude Gemini from analysis
    elif 'gpt' in model_name or 'o1-mini' in model_name or 'o3-mini' in model_name or 'o4-mini' in model_name:
        return 'OpenAI'
    elif 'qwen' in model_name:
        return 'Qwen'
    else:
        # Return the part after the slash if it exists, otherwise the whole name
        if '/' in raw_model_name:
            return raw_model_name.split('/')[-1].title()
        return raw_model_name.title()

def clean_test_case_name(raw_test_case):
    """Clean up test case names for display"""
    if not raw_test_case or raw_test_case == 'unknown':
        return 'unknown'
    
    # Clean up common test case patterns
    test_case = str(raw_test_case).strip()
    
    # Remove common prefixes/suffixes and clean up
    test_case = test_case.replace('_', ' ').replace('-', ' ')
    
    # Capitalize words properly
    words = test_case.split()
    cleaned_words = []
    for word in words:
        if word.lower() in ['ai', 'api', 'llm', 'gpt', 'nlp']:
            cleaned_words.append(word.upper())
        else:
            cleaned_words.append(word.capitalize())
    
    return ' '.join(cleaned_words)

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    print("Processing batch_thinking data from both direct_request and command tactics")
    print("Extracting test case names from metadata line and cleaning for display")
    print("Computing max score per JSONL file correctly")
    print("Excluding Gemini models from analysis")
    
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
                    'test_case': clean_test_case_name(metadata_line.get('test_case', 'unknown')),
                    'turn_type': metadata_line.get('turn_type', 'unknown'),
                    'jailbreak_tactic': metadata_line.get('jailbreak_tactic', 'unknown'),
                    'reasoning_level': extract_reasoning_level(file_path.name, metadata_line)
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
                    
            # Only include conversations with valid tactic, scores, and non-Gemini models
            if valid_data_found and conversation_scores and file_metadata['model'] is not None:
                # CORRECT SCORE COMPUTATION: Maximum score across all rounds
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
                else:
                    print(f"Unknown turn type '{turn_type}' in {file_path.name}")
                    
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

def analyze_test_cases(df, turn_type):
    """Analyze test case distribution and sample sizes"""
    
    print(f"\n=== {turn_type.upper()} TEST CASE ANALYSIS ===")
    
    if len(df) == 0:
        print("No data available")
        return []
    
    # Get test case distribution
    test_case_counts = df['test_case'].value_counts()
    print(f"Total conversations: {len(df)}")
    print(f"Unique test cases: {len(test_case_counts)}")
    print("\nTest case distribution:")
    
    test_cases_with_sufficient_data = []
    for test_case, count in test_case_counts.items():
        print(f"  {test_case}: {count} conversations")
        if count >= 10:  # Minimum threshold for analysis
            test_cases_with_sufficient_data.append(test_case)
    
    print(f"\nTest cases with sufficient data (≥10 conversations): {len(test_cases_with_sufficient_data)}")
    for test_case in test_cases_with_sufficient_data:
        test_case_data = df[df['test_case'] == test_case]
        avg_score = test_case_data['max_score'].mean()
        success_rate = (test_case_data['max_score'] >= 1.0).mean() * 100
        avg_tokens = test_case_data['avg_reasoning_tokens'].mean()
        correlation = test_case_data['avg_reasoning_tokens'].corr(test_case_data['max_score'])
        models_in_test_case = test_case_data['model'].nunique()
        print(f"  {test_case}: avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, "
              f"avg_tokens={avg_tokens:.0f}, correlation={correlation:.3f}, models={models_in_test_case}")
    
    return test_cases_with_sufficient_data

def create_reasoning_token_bins(df, test_case, turn_type):
    """Create reasoning token bins for a specific test case"""
    
    test_case_data = df[df['test_case'] == test_case].copy()
    
    if len(test_case_data) == 0:
        return test_case_data, []
    
    # Define bins
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Create bins
    test_case_data['reasoning_bin'] = pd.cut(test_case_data['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Calculate bin statistics (averaging over models)
    bin_stats = []
    for label in bin_labels:
        bin_data = test_case_data[test_case_data['reasoning_bin'] == label]
        if len(bin_data) > 0:
            avg_score = bin_data['max_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            count = len(bin_data)
            avg_tokens = bin_data['avg_reasoning_tokens'].mean()
            bin_stats.append({
                'bin': label,
                'avg_score': avg_score,
                'success_rate': success_rate,
                'count': count,
                'avg_tokens': avg_tokens
            })
        else:
            bin_stats.append({
                'bin': label,
                'avg_score': 0,
                'success_rate': 0,
                'count': 0,
                'avg_tokens': 0
            })
    
    return test_case_data, bin_stats

def create_test_case_comparison_plots(single_df, multi_df, single_test_cases, multi_test_cases):
    """Create comprehensive test case comparison plots"""
    
    print("\nGenerating test case comparison plots...")
    
    # Get all unique test cases
    all_test_cases = list(set(single_test_cases + multi_test_cases))
    
    if len(all_test_cases) == 0:
        print("No test cases with sufficient data found")
        return
    
    # Calculate grid dimensions - 5 columns for better layout
    cols = 5
    rows = math.ceil(len(all_test_cases) / cols) * 2  # 2 rows per test case (single + multi)
    
    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows))
    
    # Ensure axes is always 2D
    if rows == 1:
        axes = axes.reshape(1, -1)
    if cols == 1:
        axes = axes.reshape(-1, 1)
    
    # Color scheme for bins
    bin_colors = ['red', 'orange', 'gold', 'lightgreen', 'darkgreen']
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Plot each test case (single-turn in top row, multi-turn in bottom row)
    for i, test_case in enumerate(all_test_cases):
        # Single-turn plot (even rows)
        single_row = (i // cols) * 2
        col = i % cols
        
        if single_row < rows:
            ax = axes[single_row, col]
            
            if test_case in single_test_cases:
                test_case_data, bin_stats = create_reasoning_token_bins(single_df, test_case, "single-turn")
                
                if bin_stats:
                    bins = [stat['bin'] for stat in bin_stats if stat['count'] > 0]
                    scores = [stat['avg_score'] for stat in bin_stats if stat['count'] > 0]
                    counts = [stat['count'] for stat in bin_stats if stat['count'] > 0]
                    colors = [bin_colors[j] for j, stat in enumerate(bin_stats) if stat['count'] > 0]
                    
                    if bins and scores:
                        bars = ax.bar(bins, scores, color=colors, alpha=0.8, edgecolor='black')
                        
                        # Add value labels
                        for bar, score, count in zip(bars, scores, counts):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                                   f'{score:.3f}\n(n={count})', ha='center', va='bottom', fontsize=7)
                        
                        ax.set_ylim(0, 1)
                        ax.set_ylabel('Average Max Score', fontsize=8)
                        ax.set_title(f'Single-Turn: {test_case}\n(Total: {len(test_case_data)} conversations)', fontsize=9)
                        ax.grid(True, alpha=0.3)
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=7)
                    else:
                        ax.text(0.5, 0.5, 'No Data\nwith Reasoning', ha='center', va='center', transform=ax.transAxes)
                        ax.set_title(f'Single-Turn: {test_case}\n(No reasoning data)', fontsize=9)
                else:
                    ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'Single-Turn: {test_case}\n(No data)', fontsize=9)
            else:
                ax.text(0.5, 0.5, 'No Single-Turn\nData', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Single-Turn: {test_case}\n(No data)', fontsize=9)
        
        # Multi-turn plot (odd rows)
        multi_row = (i // cols) * 2 + 1
        
        if multi_row < rows:
            ax = axes[multi_row, col]
            
            if test_case in multi_test_cases:
                test_case_data, bin_stats = create_reasoning_token_bins(multi_df, test_case, "multi-turn")
                
                if bin_stats:
                    bins = [stat['bin'] for stat in bin_stats if stat['count'] > 0]
                    scores = [stat['avg_score'] for stat in bin_stats if stat['count'] > 0]
                    counts = [stat['count'] for stat in bin_stats if stat['count'] > 0]
                    colors = [bin_colors[j] for j, stat in enumerate(bin_stats) if stat['count'] > 0]
                    
                    if bins and scores:
                        bars = ax.bar(bins, scores, color=colors, alpha=0.8, edgecolor='black')
                        
                        # Add value labels
                        for bar, score, count in zip(bars, scores, counts):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                                   f'{score:.3f}\n(n={count})', ha='center', va='bottom', fontsize=7)
                        
                        ax.set_ylim(0, 1)
                        ax.set_ylabel('Average Max Score', fontsize=8)
                        ax.set_title(f'Multi-Turn: {test_case}\n(Total: {len(test_case_data)} conversations)', fontsize=9)
                        ax.grid(True, alpha=0.3)
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=7)
                    else:
                        ax.text(0.5, 0.5, 'No Data\nwith Reasoning', ha='center', va='center', transform=ax.transAxes)
                        ax.set_title(f'Multi-Turn: {test_case}\n(No reasoning data)', fontsize=9)
                else:
                    ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'Multi-Turn: {test_case}\n(No data)', fontsize=9)
            else:
                ax.text(0.5, 0.5, 'No Multi-Turn\nData', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Multi-Turn: {test_case}\n(No data)', fontsize=9)
    
    # Fill remaining subplots
    total_test_cases = len(all_test_cases)
    for i in range(total_test_cases, rows * cols // 2):
        single_row = (i // cols) * 2
        multi_row = (i // cols) * 2 + 1
        col = i % cols
        
        if single_row < rows:
            axes[single_row, col].axis('off')
        if multi_row < rows:
            axes[multi_row, col].axis('off')
    
    plt.tight_layout()
    plt.savefig('corrected_testcase_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_test_case_analysis_report(single_df, multi_df, single_test_cases, multi_test_cases):
    """Generate comprehensive test case analysis report"""
    
    report = f"""
# Test Case Comparison Analysis Report - Batch Thinking + Direct Request

## Dataset Overview
- **Single-Turn Test Cases with Sufficient Data (≥10 conversations)**: {len(single_test_cases)}
- **Multi-Turn Test Cases with Sufficient Data (≥10 conversations)**: {len(multi_test_cases)}
- **Total Single-Turn Conversations**: {len(single_df):,}
- **Total Multi-Turn Conversations**: {len(multi_df):,}

## Test Case Performance Analysis

### Single-Turn Test Cases
"""
    
    if single_test_cases:
        for test_case in single_test_cases:
            test_case_data = single_df[single_df['test_case'] == test_case]
            avg_score = test_case_data['max_score'].mean()
            success_rate = (test_case_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = test_case_data['avg_reasoning_tokens'].mean()
            correlation = test_case_data['avg_reasoning_tokens'].corr(test_case_data['max_score'])
            models_count = test_case_data['model'].nunique()
            
            report += f"""
**{test_case}** (n={len(test_case_data)}, {models_count} models):
- Average max score: {avg_score:.3f}
- Success rate: {success_rate:.1f}%
- Average reasoning tokens: {avg_tokens:.0f}
- Correlation (tokens vs score): {correlation:.3f}
"""
    else:
        report += "- No single-turn test cases with sufficient data\n"
    
    report += f"""
### Multi-Turn Test Cases
"""
    
    if multi_test_cases:
        for test_case in multi_test_cases:
            test_case_data = multi_df[multi_df['test_case'] == test_case]
            avg_score = test_case_data['max_score'].mean()
            success_rate = (test_case_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = test_case_data['avg_reasoning_tokens'].mean()
            correlation = test_case_data['avg_reasoning_tokens'].corr(test_case_data['max_score'])
            models_count = test_case_data['model'].nunique()
            
            report += f"""
**{test_case}** (n={len(test_case_data)}, {models_count} models):
- Average max score: {avg_score:.3f}
- Success rate: {success_rate:.1f}%
- Average reasoning tokens: {avg_tokens:.0f}
- Correlation (tokens vs score): {correlation:.3f}
"""
    else:
        report += "- No multi-turn test cases with sufficient data\n"
    
    # Compare common test cases
    common_test_cases = set(single_test_cases) & set(multi_test_cases)
    if common_test_cases:
        report += f"""
### Multi-Turn vs Single-Turn Comparison (Common Test Cases)
"""
        
        for test_case in common_test_cases:
            single_data = single_df[single_df['test_case'] == test_case]
            multi_data = multi_df[multi_df['test_case'] == test_case]
            
            single_score = single_data['max_score'].mean()
            multi_score = multi_data['max_score'].mean()
            score_diff = multi_score - single_score
            
            single_success = (single_data['max_score'] >= 1.0).mean() * 100
            multi_success = (multi_data['max_score'] >= 1.0).mean() * 100
            success_diff = multi_success - single_success
            
            report += f"""
**{test_case}**:
- Score improvement (multi vs single): {score_diff:+.3f}
- Success rate improvement: {success_diff:+.1f}%
"""
    
    return report

def main():
    """Main analysis function"""
    
    print("Starting Corrected Test Case Comparison Analysis (excluding Gemini)...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Analyze test cases
    single_test_cases = analyze_test_cases(single_df, "single-turn")
    multi_test_cases = analyze_test_cases(multi_df, "multi-turn")
    
    if not single_test_cases and not multi_test_cases:
        print("No test cases with sufficient data found!")
        return
    
    # Create test case comparison plots
    create_test_case_comparison_plots(single_df, multi_df, single_test_cases, multi_test_cases)
    
    # Generate report
    report = generate_test_case_analysis_report(single_df, multi_df, single_test_cases, multi_test_cases)
    
    # Save report
    with open('corrected_testcase_analysis_report.md', 'w') as f:
        f.write(report)
    
    print(f"\nTest case comparison analysis complete!")
    print(f"- Main visualization saved as 'corrected_testcase_comparison_analysis.png'")
    print(f"- Report saved as 'corrected_testcase_analysis_report.md'")
    print(report)

if __name__ == "__main__":
    main()