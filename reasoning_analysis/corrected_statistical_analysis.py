#!/usr/bin/env python3
"""
Corrected Statistical Analysis - Batch Thinking + Direct Request
Statistical analysis without seaborn dependency
Properly computes scores as maximum over rounds per JSONL file
Separates single-turn and multi-turn data
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

def perform_statistical_analysis(single_df, multi_df):
    """Perform comprehensive statistical analysis"""
    
    print("\n=== CORRECTED STATISTICAL ANALYSIS ===")
    
    # Basic descriptive statistics
    print("\n--- Descriptive Statistics ---")
    
    if len(single_df) > 0:
        print(f"SINGLE-TURN (n={len(single_df)}):")
        print(f"  Max Score: mean={single_df['max_score'].mean():.3f}, std={single_df['max_score'].std():.3f}")
        print(f"  Reasoning Tokens: mean={single_df['avg_reasoning_tokens'].mean():.1f}, std={single_df['avg_reasoning_tokens'].std():.1f}")
        print(f"  Success Rate: {(single_df['max_score'] >= 1.0).mean() * 100:.1f}%")
    
    if len(multi_df) > 0:
        print(f"MULTI-TURN (n={len(multi_df)}):")
        print(f"  Max Score: mean={multi_df['max_score'].mean():.3f}, std={multi_df['max_score'].std():.3f}")
        print(f"  Reasoning Tokens: mean={multi_df['avg_reasoning_tokens'].mean():.1f}, std={multi_df['avg_reasoning_tokens'].std():.1f}")
        print(f"  Success Rate: {(multi_df['max_score'] >= 1.0).mean() * 100:.1f}%")
    
    # Correlation analysis
    print("\n--- Correlation Analysis ---")
    
    if len(single_df) > 0:
        single_corr = single_df['avg_reasoning_tokens'].corr(single_df['max_score'])
        print(f"Single-Turn: Reasoning Tokens vs Max Score = {single_corr:.4f}")
    
    if len(multi_df) > 0:
        multi_corr = multi_df['avg_reasoning_tokens'].corr(multi_df['max_score'])
        print(f"Multi-Turn: Reasoning Tokens vs Max Score = {multi_corr:.4f}")
    
    # Statistical tests
    print("\n--- Statistical Tests ---")
    
    # T-test comparing single vs multi-turn scores
    if len(single_df) > 0 and len(multi_df) > 0:
        t_stat, p_value = stats.ttest_ind(single_df['max_score'], multi_df['max_score'])
        print(f"T-test (single vs multi-turn max scores): t={t_stat:.4f}, p={p_value:.4f}")
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(single_df) - 1) * single_df['max_score'].var() + 
                             (len(multi_df) - 1) * multi_df['max_score'].var()) / 
                            (len(single_df) + len(multi_df) - 2))
        cohens_d = (multi_df['max_score'].mean() - single_df['max_score'].mean()) / pooled_std
        print(f"Effect size (Cohen's d): {cohens_d:.4f}")
        
        # Mann-Whitney U test (non-parametric)
        u_stat, p_value_u = stats.mannwhitneyu(single_df['max_score'], multi_df['max_score'], alternative='two-sided')
        print(f"Mann-Whitney U test: U={u_stat:.4f}, p={p_value_u:.4f}")
    
    # Analysis by reasoning level
    print("\n--- Reasoning Level Analysis ---")
    
    for df, turn_type in [(single_df, 'single-turn'), (multi_df, 'multi-turn')]:
        if len(df) > 0:
            print(f"\n{turn_type.upper()}:")
            
            # ANOVA test
            groups = []
            group_names = []
            for level in ['low', 'medium', 'high']:
                level_data = df[df['reasoning_level'] == level]
                if len(level_data) > 0:
                    groups.append(level_data['max_score'])
                    group_names.append(level)
            
            if len(groups) > 1:
                f_stat, p_value = stats.f_oneway(*groups)
                print(f"  ANOVA (reasoning level vs max score): F={f_stat:.4f}, p={p_value:.4f}")
                
                # Post-hoc pairwise comparisons
                print("  Pairwise comparisons:")
                for i, group1 in enumerate(group_names):
                    for j, group2 in enumerate(group_names):
                        if i < j:
                            t_stat, p_val = stats.ttest_ind(groups[i], groups[j])
                            print(f"    {group1} vs {group2}: t={t_stat:.3f}, p={p_val:.3f}")

def create_statistical_plots(single_df, multi_df):
    """Create statistical visualization plots"""
    
    print("\nGenerating statistical plots...")
    
    # Create comprehensive figure
    fig = plt.figure(figsize=(20, 15))
    
    # Row 1: Score distributions
    ax1 = plt.subplot(3, 4, 1)
    if len(single_df) > 0:
        plt.hist(single_df['max_score'], bins=20, alpha=0.7, color='blue', label='Single-Turn', density=True)
    if len(multi_df) > 0:
        plt.hist(multi_df['max_score'], bins=20, alpha=0.7, color='green', label='Multi-Turn', density=True)
    plt.xlabel('Maximum Score')
    plt.ylabel('Density')
    plt.title('Score Distributions')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Box plots by turn type
    ax2 = plt.subplot(3, 4, 2)
    data_to_plot = []
    labels = []
    if len(single_df) > 0:
        data_to_plot.append(single_df['max_score'])
        labels.append('Single-Turn')
    if len(multi_df) > 0:
        data_to_plot.append(multi_df['max_score'])
        labels.append('Multi-Turn')
    
    if data_to_plot:
        plt.boxplot(data_to_plot, labels=labels)
        plt.ylabel('Maximum Score')
        plt.title('Score Box Plots by Turn Type')
        plt.grid(True, alpha=0.3)
    
    # Correlation scatter plots
    ax3 = plt.subplot(3, 4, 3)
    if len(single_df) > 0:
        plt.scatter(single_df['avg_reasoning_tokens'], single_df['max_score'], 
                   alpha=0.6, s=30, color='blue', label='Single-Turn')
        # Add trend line
        z = np.polyfit(single_df['avg_reasoning_tokens'], single_df['max_score'], 1)
        p = np.poly1d(z)
        plt.plot(single_df['avg_reasoning_tokens'], p(single_df['avg_reasoning_tokens']), 
                "b--", alpha=0.8, linewidth=2)
    
    if len(multi_df) > 0:
        plt.scatter(multi_df['avg_reasoning_tokens'], multi_df['max_score'], 
                   alpha=0.6, s=30, color='green', label='Multi-Turn')
        # Add trend line
        z = np.polyfit(multi_df['avg_reasoning_tokens'], multi_df['max_score'], 1)
        p = np.poly1d(z)
        plt.plot(multi_df['avg_reasoning_tokens'], p(multi_df['avg_reasoning_tokens']), 
                "g--", alpha=0.8, linewidth=2)
    
    plt.xlabel('Average Reasoning Tokens')
    plt.ylabel('Maximum Score')
    plt.title('Reasoning Tokens vs Score')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Success rate by reasoning level
    ax4 = plt.subplot(3, 4, 4)
    reasoning_levels = ['low', 'medium', 'high']
    
    single_success_rates = []
    multi_success_rates = []
    
    for level in reasoning_levels:
        if len(single_df) > 0:
            level_data = single_df[single_df['reasoning_level'] == level]
            success_rate = (level_data['max_score'] >= 1.0).mean() * 100 if len(level_data) > 0 else 0
            single_success_rates.append(success_rate)
        else:
            single_success_rates.append(0)
        
        if len(multi_df) > 0:
            level_data = multi_df[multi_df['reasoning_level'] == level]
            success_rate = (level_data['max_score'] >= 1.0).mean() * 100 if len(level_data) > 0 else 0
            multi_success_rates.append(success_rate)
        else:
            multi_success_rates.append(0)
    
    x = np.arange(len(reasoning_levels))
    width = 0.35
    
    if len(single_df) > 0:
        plt.bar(x - width/2, single_success_rates, width, label='Single-Turn', color='blue', alpha=0.7)
    if len(multi_df) > 0:
        plt.bar(x + width/2, multi_success_rates, width, label='Multi-Turn', color='green', alpha=0.7)
    
    plt.xlabel('Reasoning Level')
    plt.ylabel('Success Rate (%)')
    plt.title('Success Rate by Reasoning Level')
    plt.xticks(x, reasoning_levels)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Row 2: Token bin analysis
    ax5 = plt.subplot(3, 4, 5)
    token_bins = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    single_bin_scores = []
    multi_bin_scores = []
    
    for i in range(len(token_bins)-1):
        min_val, max_val = token_bins[i], token_bins[i+1]
        
        if len(single_df) > 0:
            if max_val == float('inf'):
                single_bin_data = single_df[single_df['avg_reasoning_tokens'] >= min_val]
            else:
                single_bin_data = single_df[(single_df['avg_reasoning_tokens'] >= min_val) & 
                                          (single_df['avg_reasoning_tokens'] < max_val)]
            single_bin_scores.append(single_bin_data['max_score'].mean() if len(single_bin_data) > 0 else 0)
        else:
            single_bin_scores.append(0)
        
        if len(multi_df) > 0:
            if max_val == float('inf'):
                multi_bin_data = multi_df[multi_df['avg_reasoning_tokens'] >= min_val]
            else:
                multi_bin_data = multi_df[(multi_df['avg_reasoning_tokens'] >= min_val) & 
                                        (multi_df['avg_reasoning_tokens'] < max_val)]
            multi_bin_scores.append(multi_bin_data['max_score'].mean() if len(multi_bin_data) > 0 else 0)
        else:
            multi_bin_scores.append(0)
    
    x = np.arange(len(bin_labels))
    width = 0.35
    
    if len(single_df) > 0:
        plt.bar(x - width/2, single_bin_scores, width, label='Single-Turn', color='blue', alpha=0.7)
    if len(multi_df) > 0:
        plt.bar(x + width/2, multi_bin_scores, width, label='Multi-Turn', color='green', alpha=0.7)
    
    plt.xlabel('Reasoning Token Bins')
    plt.ylabel('Average Max Score')
    plt.title('Average Score by Token Bins')
    plt.xticks(x, bin_labels, rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Reasoning token distributions
    ax6 = plt.subplot(3, 4, 6)
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
    
    # Summary statistics
    ax7 = plt.subplot(3, 4, 7)
    if len(single_df) > 0 and len(multi_df) > 0:
        categories = ['Avg Score', 'Success Rate', 'Avg Tokens']
        single_values = [
            single_df['max_score'].mean(),
            (single_df['max_score'] >= 1.0).mean() * 100,
            single_df['avg_reasoning_tokens'].mean() / 1000  # Scale for visibility
        ]
        multi_values = [
            multi_df['max_score'].mean(),
            (multi_df['max_score'] >= 1.0).mean() * 100,
            multi_df['avg_reasoning_tokens'].mean() / 1000  # Scale for visibility
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        plt.bar(x - width/2, single_values, width, label='Single-Turn', color='blue', alpha=0.7)
        plt.bar(x + width/2, multi_values, width, label='Multi-Turn', color='green', alpha=0.7)
        
        plt.xlabel('Metrics')
        plt.ylabel('Values')
        plt.title('Summary Comparison\n(Tokens scaled by 1000)')
        plt.xticks(x, categories)
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # Additional plots for remaining subplots
    for i in range(8, 12):
        ax = plt.subplot(3, 4, i)
        ax.text(0.5, 0.5, f'Additional\nAnalysis\n{i-7}', ha='center', va='center', 
                transform=ax.transAxes, fontsize=12)
    
    plt.tight_layout()
    plt.savefig('corrected_statistical_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_statistical_report(single_df, multi_df):
    """Generate comprehensive statistical report"""
    
    report = f"""
# Corrected Statistical Analysis Report - Batch Thinking + Direct Request

## Dataset Overview
- **Single-Turn Conversations**: {len(single_df):,}
- **Multi-Turn Conversations**: {len(multi_df):,}
- **Total Conversations**: {len(single_df) + len(multi_df):,}

## Corrected Score Computation
- **Method**: Maximum score across all rounds per JSONL file
- **Rationale**: Each JSONL represents one test case; we want the best performance achieved

## Key Statistical Findings

### Descriptive Statistics
"""
    
    if len(single_df) > 0:
        report += f"""
**Single-Turn (n={len(single_df)}):**
- Mean max score: {single_df['max_score'].mean():.3f} (SD={single_df['max_score'].std():.3f})
- Success rate: {(single_df['max_score'] >= 1.0).mean() * 100:.1f}%
- Mean reasoning tokens: {single_df['avg_reasoning_tokens'].mean():.1f} (SD={single_df['avg_reasoning_tokens'].std():.1f})
"""
    
    if len(multi_df) > 0:
        report += f"""
**Multi-Turn (n={len(multi_df)}):**
- Mean max score: {multi_df['max_score'].mean():.3f} (SD={multi_df['max_score'].std():.3f})
- Success rate: {(multi_df['max_score'] >= 1.0).mean() * 100:.1f}%
- Mean reasoning tokens: {multi_df['avg_reasoning_tokens'].mean():.1f} (SD={multi_df['avg_reasoning_tokens'].std():.1f})
"""
    
    if len(single_df) > 0 and len(multi_df) > 0:
        score_diff = multi_df['max_score'].mean() - single_df['max_score'].mean()
        success_diff = (multi_df['max_score'] >= 1.0).mean() - (single_df['max_score'] >= 1.0).mean()
        
        report += f"""
### Multi-Turn Advantage
- **Score difference**: {score_diff:+.3f} (multi-turn higher)
- **Success rate difference**: {success_diff * 100:+.1f}% (multi-turn higher)
"""
    
    report += f"""
### Correlation Analysis
"""
    
    if len(single_df) > 0:
        single_corr = single_df['avg_reasoning_tokens'].corr(single_df['max_score'])
        report += f"- **Single-Turn**: Reasoning tokens vs max score = {single_corr:.4f}\n"
    
    if len(multi_df) > 0:
        multi_corr = multi_df['avg_reasoning_tokens'].corr(multi_df['max_score'])
        report += f"- **Multi-Turn**: Reasoning tokens vs max score = {multi_corr:.4f}\n"
    
    if len(single_df) > 0 and len(multi_df) > 0:
        report += f"""
### Statistical Significance Tests
"""
        
        # T-test
        t_stat, p_value = stats.ttest_ind(single_df['max_score'], multi_df['max_score'])
        report += f"- **T-test** (single vs multi-turn scores): t={t_stat:.4f}, p={p_value:.4f}\n"
        
        # Effect size
        pooled_std = np.sqrt(((len(single_df) - 1) * single_df['max_score'].var() + 
                             (len(multi_df) - 1) * multi_df['max_score'].var()) / 
                            (len(single_df) + len(multi_df) - 2))
        cohens_d = (multi_df['max_score'].mean() - single_df['max_score'].mean()) / pooled_std
        report += f"- **Effect size** (Cohen's d): {cohens_d:.4f}\n"
        
        # Interpretation
        if abs(cohens_d) < 0.2:
            effect_size_interpretation = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_size_interpretation = "small"
        elif abs(cohens_d) < 0.8:
            effect_size_interpretation = "medium"
        else:
            effect_size_interpretation = "large"
        
        report += f"- **Effect size interpretation**: {effect_size_interpretation}\n"
    
    return report

def main():
    """Main analysis function"""
    
    print("Starting Corrected Statistical Analysis...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Perform statistical analysis
    perform_statistical_analysis(single_df, multi_df)
    
    # Create visualizations
    create_statistical_plots(single_df, multi_df)
    
    # Generate report
    report = generate_statistical_report(single_df, multi_df)
    
    # Save report
    with open('corrected_statistical_analysis_report.md', 'w') as f:
        f.write(report)
    
    print(f"\nStatistical analysis complete!")
    print(f"- Visualization saved as 'corrected_statistical_analysis.png'")
    print(f"- Report saved as 'corrected_statistical_analysis_report.md'")
    print(report)

if __name__ == "__main__":
    main()