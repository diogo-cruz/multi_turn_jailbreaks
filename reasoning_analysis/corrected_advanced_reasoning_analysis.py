#!/usr/bin/env python3
"""
Corrected Advanced Reasoning Token Analysis - Batch Thinking + Direct Request
Advanced analysis with statistical tests using seaborn
Properly computes scores as maximum over rounds per JSONL file
Separates single-turn and multi-turn data
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from {}".format(data_dir))
    print("Filtering for batch_thinking data and direct_request tactic only")
    print("Computing max score per JSONL file correctly")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found {} JSONL files".format(len(jsonl_files)))
    
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
                            'round': data.get('round', 1),
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
                    'total_reasoning_tokens': sum(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0,
                    'num_reasoning_rounds': len(conversation_reasoning_tokens),
                    'num_total_rounds': len(conversation_scores),
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
    
    print(f"\n=== {turn_type.upper()} ADVANCED REASONING ANALYSIS ===")
    print(f"Total conversations: {len(df)}")
    
    if len(df) == 0:
        print("No data available")
        return None
    
    print(f"Conversations with reasoning tokens > 0: {len(df[df['avg_reasoning_tokens'] > 0])}")
    
    # Success rate statistics
    df['success'] = df['max_score'] >= 1.0
    overall_success_rate = df['success'].mean() * 100
    
    print(f"\nOverall Success Rate: {overall_success_rate:.2f}%")
    print(f"Average Max Score: {df['max_score'].mean():.3f}")
    
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
        return None
    
    # Group by reasoning level
    level_stats = df.groupby('reasoning_level').agg({
        'avg_reasoning_tokens': ['count', 'mean', 'std'],
        'max_score': 'mean',
        'success': 'mean'
    }).round(4)
    
    level_stats.columns = ['Count', 'Avg_Reasoning_Tokens', 'Std_Reasoning_Tokens', 
                          'Avg_Max_Score', 'Success_Rate']
    
    print(level_stats)
    
    return level_stats

def create_advanced_visualizations(single_df, multi_df, output_dir="corrected_advanced_reasoning_plots"):
    """Create advanced visualizations with seaborn"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Combine data for some plots
    if len(single_df) > 0:
        single_df_plot = single_df.copy()
        single_df_plot['turn_type'] = 'Single-Turn'
    else:
        single_df_plot = pd.DataFrame()
    
    if len(multi_df) > 0:
        multi_df_plot = multi_df.copy()
        multi_df_plot['turn_type'] = 'Multi-Turn'
    else:
        multi_df_plot = pd.DataFrame()
    
    combined_df = pd.concat([single_df_plot, multi_df_plot], ignore_index=True)
    
    if len(combined_df) == 0:
        print("No data available for visualization")
        return
    
    # 1. Scatter plot with regression lines by turn type
    plt.figure(figsize=(12, 8))
    
    if len(combined_df) > 0:
        # Add jitter to scores for better visualization
        combined_df['score_jitter'] = combined_df['max_score'] + np.random.normal(0, 0.02, len(combined_df))
        
        # Create scatter plot with different colors for turn types
        sns.scatterplot(data=combined_df, x='avg_reasoning_tokens', y='score_jitter', 
                       hue='turn_type', style='success', alpha=0.7, s=50)
        
        # Add regression lines
        sns.regplot(data=combined_df[combined_df['turn_type'] == 'Single-Turn'], 
                   x='avg_reasoning_tokens', y='max_score', 
                   scatter=False, color='blue', label='Single-Turn Trend')
        sns.regplot(data=combined_df[combined_df['turn_type'] == 'Multi-Turn'], 
                   x='avg_reasoning_tokens', y='max_score', 
                   scatter=False, color='green', label='Multi-Turn Trend')
    
    plt.xlabel('Average Reasoning Tokens')
    plt.ylabel('Maximum Score')
    plt.title('Reasoning Tokens vs Maximum Score by Turn Type')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'reasoning_vs_score_by_turn_type.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. Box plots by reasoning level and turn type
    plt.figure(figsize=(14, 8))
    
    plt.subplot(1, 2, 1)
    if len(combined_df) > 0:
        sns.boxplot(data=combined_df, x='reasoning_level', y='max_score', hue='turn_type')
        plt.title('Max Score Distribution by Reasoning Level')
        plt.xticks(rotation=45)
    
    plt.subplot(1, 2, 2)
    if len(combined_df) > 0:
        sns.boxplot(data=combined_df, x='reasoning_level', y='avg_reasoning_tokens', hue='turn_type')
        plt.title('Reasoning Tokens Distribution by Level')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'boxplots_by_reasoning_level.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. Heatmap: Turn Type vs Reasoning Level Success Rates
    plt.figure(figsize=(10, 6))
    
    if len(combined_df) > 0:
        # Create pivot table for heatmap
        pivot_table = combined_df.groupby(['turn_type', 'reasoning_level'])['success'].mean().unstack()
        pivot_table = pivot_table.fillna(0) * 100  # Convert to percentage
        
        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='RdYlGn', 
                   cbar_kws={'label': 'Success Rate (%)'})
        plt.title('Success Rate by Turn Type and Reasoning Level')
        plt.xlabel('Reasoning Level')
        plt.ylabel('Turn Type')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'success_rate_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 4. Distribution comparisons
    plt.figure(figsize=(15, 10))
    
    # Score distributions
    plt.subplot(2, 3, 1)
    if len(single_df) > 0:
        plt.hist(single_df['max_score'], bins=20, alpha=0.7, color='blue', label='Single-Turn', density=True)
    if len(multi_df) > 0:
        plt.hist(multi_df['max_score'], bins=20, alpha=0.7, color='green', label='Multi-Turn', density=True)
    plt.xlabel('Maximum Score')
    plt.ylabel('Density')
    plt.title('Score Distributions')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Reasoning token distributions (non-zero)
    plt.subplot(2, 3, 2)
    if len(single_df) > 0:
        single_nonzero = single_df[single_df['avg_reasoning_tokens'] > 0]['avg_reasoning_tokens']
        if len(single_nonzero) > 0:
            plt.hist(single_nonzero, bins=20, alpha=0.7, color='blue', label='Single-Turn', density=True)
    if len(multi_df) > 0:
        multi_nonzero = multi_df[multi_df['avg_reasoning_tokens'] > 0]['avg_reasoning_tokens']
        if len(multi_nonzero) > 0:
            plt.hist(multi_nonzero, bins=20, alpha=0.7, color='green', label='Multi-Turn', density=True)
    plt.xlabel('Average Reasoning Tokens')
    plt.ylabel('Density')
    plt.title('Reasoning Token Distributions\n(excluding zeros)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Success rate by token bins
    plt.subplot(2, 3, 3)
    token_bins = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    single_bin_success = []
    multi_bin_success = []
    
    for i in range(len(token_bins)-1):
        min_val, max_val = token_bins[i], token_bins[i+1]
        
        if len(single_df) > 0:
            if max_val == float('inf'):
                single_bin_data = single_df[single_df['avg_reasoning_tokens'] >= min_val]
            else:
                single_bin_data = single_df[(single_df['avg_reasoning_tokens'] >= min_val) & 
                                          (single_df['avg_reasoning_tokens'] < max_val)]
            single_bin_success.append(single_bin_data['success'].mean() * 100 if len(single_bin_data) > 0 else 0)
        else:
            single_bin_success.append(0)
        
        if len(multi_df) > 0:
            if max_val == float('inf'):
                multi_bin_data = multi_df[multi_df['avg_reasoning_tokens'] >= min_val]
            else:
                multi_bin_data = multi_df[(multi_df['avg_reasoning_tokens'] >= min_val) & 
                                        (multi_df['avg_reasoning_tokens'] < max_val)]
            multi_bin_success.append(multi_bin_data['success'].mean() * 100 if len(multi_bin_data) > 0 else 0)
        else:
            multi_bin_success.append(0)
    
    x = np.arange(len(bin_labels))
    width = 0.35
    
    plt.bar(x - width/2, single_bin_success, width, label='Single-Turn', color='blue', alpha=0.7)
    plt.bar(x + width/2, multi_bin_success, width, label='Multi-Turn', color='green', alpha=0.7)
    
    plt.xlabel('Reasoning Token Bins')
    plt.ylabel('Success Rate (%)')
    plt.title('Success Rate by Token Bins')
    plt.xticks(x, bin_labels, rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Additional summary plots
    plt.subplot(2, 3, 4)
    if len(combined_df) > 0:
        summary_data = combined_df.groupby('turn_type').agg({
            'max_score': 'mean',
            'success': lambda x: x.mean() * 100,
            'avg_reasoning_tokens': 'mean'
        }).round(3)
        
        turn_types = summary_data.index
        avg_scores = summary_data['max_score']
        
        bars = plt.bar(turn_types, avg_scores, color=['blue', 'green'], alpha=0.7)
        plt.ylabel('Average Maximum Score')
        plt.title('Average Score by Turn Type')
        plt.ylim(0, 1)
        
        for bar, score in zip(bars, avg_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{score:.3f}', ha='center', va='bottom')
    
    plt.subplot(2, 3, 5)
    # Correlation comparison
    if len(single_df) > 0 and len(multi_df) > 0:
        single_corr = single_df['avg_reasoning_tokens'].corr(single_df['max_score'])
        multi_corr = multi_df['avg_reasoning_tokens'].corr(multi_df['max_score'])
        
        correlations = [single_corr, multi_corr]
        turn_types = ['Single-Turn', 'Multi-Turn']
        
        bars = plt.bar(turn_types, correlations, color=['blue', 'green'], alpha=0.7)
        plt.ylabel('Correlation (Reasoning Tokens vs Score)')
        plt.title('Correlation Comparison')
        plt.ylim(-1, 1)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        for bar, corr in zip(bars, correlations):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{corr:.3f}', ha='center', va='bottom')
    
    plt.subplot(2, 3, 6)
    # Sample size comparison
    if len(single_df) > 0 and len(multi_df) > 0:
        sample_sizes = [len(single_df), len(multi_df)]
        turn_types = ['Single-Turn', 'Multi-Turn']
        
        bars = plt.bar(turn_types, sample_sizes, color=['blue', 'green'], alpha=0.7)
        plt.ylabel('Number of Conversations')
        plt.title('Sample Size Comparison')
        
        for bar, size in zip(bars, sample_sizes):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                    f'{size}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def perform_statistical_tests(single_df, multi_df):
    """Perform statistical tests"""
    
    print("\n=== STATISTICAL TESTS ===")
    
    # T-test comparing single vs multi-turn scores
    if len(single_df) > 0 and len(multi_df) > 0:
        t_stat, p_value = stats.ttest_ind(single_df['max_score'], multi_df['max_score'])
        print(f"T-test (single vs multi-turn max scores): t={t_stat:.4f}, p={p_value:.4f}")
        
        # Mann-Whitney U test (non-parametric alternative)
        u_stat, p_value_u = stats.mannwhitneyu(single_df['max_score'], multi_df['max_score'], alternative='two-sided')
        print(f"Mann-Whitney U test: U={u_stat:.4f}, p={p_value_u:.4f}")
    
    # Chi-square test for success rates by reasoning level
    for df, turn_type in [(single_df, 'single-turn'), (multi_df, 'multi-turn')]:
        if len(df) > 0:
            contingency = pd.crosstab(df['reasoning_level'], df['success'])
            if contingency.shape[0] > 1 and contingency.shape[1] > 1:
                chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
                print(f"Chi-square test ({turn_type} reasoning level vs success): χ²={chi2:.4f}, p={p_val:.4f}")

def generate_summary_report(single_df, multi_df, single_stats, multi_stats):
    """Generate a comprehensive summary report"""
    
    report = f"""
# Corrected Reasoning Token Analysis Report - Batch Thinking + Direct Request

## Dataset Summary
- **Single-Turn Conversations**: {len(single_df):,}
- **Multi-Turn Conversations**: {len(multi_df):,}
- **Total Conversations**: {len(single_df) + len(multi_df):,}
- **Scoring Method**: Maximum score across all rounds per JSONL file

## Key Findings

### Single-Turn Results
"""
    
    if single_stats:
        report += f"""- **Average Max Score**: {single_stats['mean_score']:.3f}
- **Success Rate**: {single_stats['overall_success_rate']:.2f}%
- **Correlation (Tokens vs Score)**: {single_stats['reasoning_score_corr']:.4f}
"""
    else:
        report += "- No single-turn data available\n"
    
    report += f"""
### Multi-Turn Results
"""
    
    if multi_stats:
        report += f"""- **Average Max Score**: {multi_stats['mean_score']:.3f}
- **Success Rate**: {multi_stats['overall_success_rate']:.2f}%
- **Correlation (Tokens vs Score)**: {multi_stats['reasoning_score_corr']:.4f}
"""
    else:
        report += "- No multi-turn data available\n"
    
    report += f"""
### Key Insights
"""
    
    if single_stats and multi_stats:
        score_diff = multi_stats['mean_score'] - single_stats['mean_score']
        success_diff = multi_stats['overall_success_rate'] - single_stats['overall_success_rate']
        
        report += f"""- **Multi-turn advantage**: {score_diff:+.3f} higher average score, {success_diff:+.1f}% higher success rate
- **Correlation difference**: Single-turn has {'stronger' if single_stats['reasoning_score_corr'] > multi_stats['reasoning_score_corr'] else 'weaker'} correlation
"""
    
    return report

def main():
    """Main analysis function"""
    
    print("Starting Corrected Advanced Reasoning Token Analysis...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Perform analyses
    single_stats = analyze_reasoning_correlation(single_df, "single-turn")
    single_level_stats = analyze_by_reasoning_level(single_df, "single-turn")
    
    multi_stats = analyze_reasoning_correlation(multi_df, "multi-turn")
    multi_level_stats = analyze_by_reasoning_level(multi_df, "multi-turn")
    
    # Create visualizations
    print("\nGenerating advanced visualizations...")
    create_advanced_visualizations(single_df, multi_df)
    
    # Statistical tests
    perform_statistical_tests(single_df, multi_df)
    
    # Generate summary report
    report = generate_summary_report(single_df, multi_df, single_stats, multi_stats)
    
    # Save report
    with open('corrected_advanced_reasoning_analysis_report.md', 'w') as f:
        f.write(report)
    
    print(f"\nAdvanced analysis complete!")
    print(f"- Visualizations saved to 'corrected_advanced_reasoning_plots/' directory")
    print(f"- Summary report saved to 'corrected_advanced_reasoning_analysis_report.md'")
    print(report)

if __name__ == "__main__":
    main()