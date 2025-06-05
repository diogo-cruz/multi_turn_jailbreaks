#!/usr/bin/env python3
"""
Reasoning Token Analysis
Analyzes the correlation between reasoning token usage and jailbreak success rates
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict
import glob
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def load_batch_thinking_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load all JSONL files from batch_thinking directory"""
    data_dir = Path(data_dir)
    all_data = []
    
    print("Loading data from {}".format(data_dir))
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found {} JSONL files".format(len(jsonl_files)))
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
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
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(all_data)} records")
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
    
    print("\n=== REASONING TOKEN ANALYSIS ===")
    print(f"Total records: {len(df)}")
    print(f"Records with reasoning tokens > 0: {len(df[df['reasoning_tokens'] > 0])}")
    
    # Basic statistics
    print(f"\nReasoning Token Statistics:")
    print(f"Min: {df['reasoning_tokens'].min()}")
    print(f"Max: {df['reasoning_tokens'].max()}")
    print(f"Mean: {df['reasoning_tokens'].mean():.2f}")
    print(f"Median: {df['reasoning_tokens'].median():.2f}")
    
    # Success rate statistics
    # Handle mixed data types in success_score
    df['success_score_numeric'] = pd.to_numeric(df['success_score'], errors='coerce')
    df['success'] = (df['success_score_numeric'] > 0.5) | (df['goal_achieved'] == True)
    overall_success_rate = df['success'].mean() * 100
    print(f"\nOverall Success Rate: {overall_success_rate:.2f}%")
    
    # Correlation analysis
    reasoning_success_corr = df['reasoning_tokens'].corr(df['success'])
    reasoning_score_corr = df['reasoning_tokens'].corr(df['success_score_numeric'])
    
    print(f"\nCorrelations:")
    print(f"Reasoning Tokens vs Success (binary): {reasoning_success_corr:.4f}")
    print(f"Reasoning Tokens vs Success Score: {reasoning_score_corr:.4f}")
    
    return {
        'reasoning_success_corr': reasoning_success_corr,
        'reasoning_score_corr': reasoning_score_corr,
        'overall_success_rate': overall_success_rate
    }

def analyze_by_reasoning_level(df):
    """Analyze success rates by reasoning level"""
    
    print("\n=== ANALYSIS BY REASONING LEVEL ===")
    
    # Group by reasoning level
    level_stats = df.groupby('reasoning_level').agg({
        'reasoning_tokens': ['count', 'mean', 'std'],
        'success': 'mean',
        'success_score_numeric': 'mean'
    }).round(4)
    
    level_stats.columns = ['Count', 'Avg_Reasoning_Tokens', 'Std_Reasoning_Tokens', 
                          'Success_Rate', 'Avg_Success_Score']
    
    print(level_stats)
    
    return level_stats

def analyze_by_model(df):
    """Analyze correlation by model"""
    
    print("\n=== ANALYSIS BY MODEL ===")
    
    model_stats = []
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        if len(model_df) < 5:  # Skip models with too few samples
            continue
            
        corr_success = model_df['reasoning_tokens'].corr(model_df['success'])
        corr_score = model_df['reasoning_tokens'].corr(model_df['success_score_numeric'])
        
        model_stats.append({
            'model': model,
            'sample_count': len(model_df),
            'avg_reasoning_tokens': model_df['reasoning_tokens'].mean(),
            'success_rate': model_df['success'].mean(),
            'corr_tokens_success': corr_success,
            'corr_tokens_score': corr_score
        })
    
    model_df = pd.DataFrame(model_stats).sort_values('corr_tokens_success', ascending=False)
    print(model_df.round(4))
    
    return model_df

def create_visualizations(df, output_dir="reasoning_analysis_plots"):
    """Create visualizations for reasoning token analysis"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Scatter plot: Reasoning tokens vs Success score
    plt.figure(figsize=(12, 8))
    
    # Add jitter to success scores for better visualization
    df_plot = df.copy()
    df_plot['success_jitter'] = df_plot['success_score_numeric'] + np.random.normal(0, 0.02, len(df_plot))
    
    scatter = plt.scatter(df_plot['reasoning_tokens'], df_plot['success_jitter'], 
                         c=df_plot['success'], cmap='RdYlGn', alpha=0.6, s=30)
    
    plt.xlabel('Reasoning Tokens')
    plt.ylabel('Success Score')
    plt.title('Reasoning Tokens vs Jailbreak Success Score')
    plt.colorbar(scatter, label='Success (0=Failed, 1=Succeeded)')
    
    # Add trend line
    if len(df[df['reasoning_tokens'] > 0]) > 1:
        valid_data = df.dropna(subset=['reasoning_tokens', 'success_score_numeric'])
        if len(valid_data) > 1:
            z = np.polyfit(valid_data['reasoning_tokens'], valid_data['success_score_numeric'], 1)
            p = np.poly1d(z)
            plt.plot(valid_data['reasoning_tokens'], p(valid_data['reasoning_tokens']), "r--", alpha=0.8, linewidth=2)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'reasoning_tokens_vs_success_scatter.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. Box plot by reasoning level
    plt.figure(figsize=(12, 6))
    
    # Success rate by reasoning level
    plt.subplot(1, 2, 1)
    reasoning_levels = ['none', 'low', 'medium', 'high']
    success_by_level = [df[df['reasoning_level'] == level]['success'].mean() * 100 
                       for level in reasoning_levels if level in df['reasoning_level'].values]
    available_levels = [level for level in reasoning_levels if level in df['reasoning_level'].values]
    
    bars = plt.bar(available_levels, success_by_level, color=['red', 'orange', 'yellow', 'green'][:len(available_levels)])
    plt.ylabel('Success Rate (%)')
    plt.title('Success Rate by Reasoning Level')
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars, success_by_level):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{value:.1f}%', ha='center', va='bottom')
    
    # Average reasoning tokens by level
    plt.subplot(1, 2, 2)
    avg_tokens_by_level = [df[df['reasoning_level'] == level]['reasoning_tokens'].mean() 
                          for level in available_levels]
    
    bars = plt.bar(available_levels, avg_tokens_by_level, color=['red', 'orange', 'yellow', 'green'][:len(available_levels)])
    plt.ylabel('Average Reasoning Tokens')
    plt.title('Average Reasoning Tokens by Level')
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars, avg_tokens_by_level):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{value:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'reasoning_level_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. Heatmap: Model vs Reasoning Level Success Rates
    plt.figure(figsize=(14, 8))
    
    # Create pivot table for heatmap
    models_with_enough_data = df['model'].value_counts()[df['model'].value_counts() >= 10].index
    df_filtered = df[df['model'].isin(models_with_enough_data)]
    
    if len(df_filtered) > 0:
        pivot_table = df_filtered.groupby(['model', 'reasoning_level'])['success'].mean().unstack()
        pivot_table = pivot_table.fillna(0) * 100  # Convert to percentage
        
        sns.heatmap(pivot_table, annot=True, fmt='.1f', cmap='RdYlGn', 
                   cbar_kws={'label': 'Success Rate (%)'})
        plt.title('Success Rate by Model and Reasoning Level')
        plt.xlabel('Reasoning Level')
        plt.ylabel('Model')
        plt.tight_layout()
        plt.savefig(output_dir / 'model_reasoning_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    # 4. Distribution of reasoning tokens
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    df_with_reasoning = df[df['reasoning_tokens'] > 0]
    plt.hist(df_with_reasoning['reasoning_tokens'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.xlabel('Reasoning Tokens')
    plt.ylabel('Frequency')
    plt.title('Distribution of Reasoning Tokens\n(excluding zero tokens)')
    
    plt.subplot(1, 2, 2)
    # Success rate by reasoning token bins
    df_with_reasoning['token_bins'] = pd.cut(df_with_reasoning['reasoning_tokens'], 
                                           bins=10, labels=False)
    bin_success = df_with_reasoning.groupby('token_bins')['success'].mean() * 100
    bin_centers = df_with_reasoning.groupby('token_bins')['reasoning_tokens'].mean()
    
    plt.plot(bin_centers, bin_success, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Average Reasoning Tokens (binned)')
    plt.ylabel('Success Rate (%)')
    plt.title('Success Rate vs Reasoning Token Usage')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'reasoning_tokens_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_summary_report(df, correlations, level_stats, model_stats):
    """Generate a summary report of the analysis"""
    
    report = f"""
# Reasoning Token Analysis Report

## Dataset Summary
- Total records analyzed: {len(df):,}
- Records with reasoning tokens > 0: {len(df[df['reasoning_tokens'] > 0]):,}
- Unique models: {df['model'].nunique()}
- Unique test cases: {df['test_case'].nunique()}

## Key Findings

### Overall Correlations
- **Reasoning Tokens vs Success Rate**: {correlations['reasoning_success_corr']:.4f}
- **Reasoning Tokens vs Success Score**: {correlations['reasoning_score_corr']:.4f}
- **Overall Success Rate**: {correlations['overall_success_rate']:.2f}%

### Reasoning Token Statistics
- Min reasoning tokens: {df['reasoning_tokens'].min()}
- Max reasoning tokens: {df['reasoning_tokens'].max()}
- Average reasoning tokens: {df['reasoning_tokens'].mean():.2f}
- Median reasoning tokens: {df['reasoning_tokens'].median():.2f}

### Success Rate by Reasoning Level
"""
    
    for level in level_stats.index:
        success_rate = level_stats.loc[level, 'Success_Rate'] * 100
        avg_tokens = level_stats.loc[level, 'Avg_Reasoning_Tokens']
        count = level_stats.loc[level, 'Count']
        report += f"- **{level.title()}**: {success_rate:.2f}% success rate (avg {avg_tokens:.0f} tokens, n={count})\n"
    
    report += f"""
### Statistical Significance
"""
    
    # Perform statistical tests
    reasoning_present = df[df['reasoning_tokens'] > 0]['success']
    reasoning_absent = df[df['reasoning_tokens'] == 0]['success']
    
    if len(reasoning_present) > 0 and len(reasoning_absent) > 0:
        t_stat, p_value = stats.ttest_ind(reasoning_present, reasoning_absent)
        report += f"- T-test (reasoning vs no reasoning): t={t_stat:.4f}, p={p_value:.4f}\n"
    
    report += f"""
### Interpretation
"""
    
    if correlations['reasoning_success_corr'] > 0.1:
        report += "- **Positive correlation**: Higher reasoning token usage is associated with higher success rates\n"
    elif correlations['reasoning_success_corr'] < -0.1:
        report += "- **Negative correlation**: Higher reasoning token usage is associated with lower success rates\n"
    else:
        report += "- **Weak correlation**: Limited relationship between reasoning token usage and success rates\n"
    
    return report

def main():
    """Main analysis function"""
    
    print("Starting Reasoning Token Analysis...")
    
    # Load data
    df = load_batch_thinking_data()
    
    if len(df) == 0:
        print("No data found! Check if the batch_thinking directory exists and contains JSONL files.")
        return
    
    # Perform analyses
    correlations = analyze_reasoning_correlation(df)
    level_stats = analyze_by_reasoning_level(df)
    model_stats = analyze_by_model(df)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(df)
    
    # Generate summary report
    report = generate_summary_report(df, correlations, level_stats, model_stats)
    
    # Save report
    with open('reasoning_analysis_report.md', 'w') as f:
        f.write(report)
    
    print(f"\nAnalysis complete!")
    print(f"- Visualizations saved to 'reasoning_analysis_plots/' directory")
    print(f"- Summary report saved to 'reasoning_analysis_report.md'")
    print(report)

if __name__ == "__main__":
    main()