#!/usr/bin/env python3
"""
Script to compare human and AI meta-evaluator results
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import numpy as np
import os

def load_human_evaluations(filepath):
    """Load human evaluations from JSONL file"""
    human_data = []
    with open(filepath, 'r') as f:
        for line in f:
            human_data.append(json.loads(line.strip()))
    return pd.DataFrame(human_data)

def load_ai_evaluations():
    """Load AI evaluations from the most recent CSV file"""
    # Try combined results first, then fall back to random 100
    combined_file = 'combined_meta_evaluation_results/issue_scores_combined_20250617_064347.csv'
    random_file = 'random_100_meta_evaluation_results/issue_scores_20250617_005322.csv'
    
    if os.path.exists(combined_file):
        print(f"Using combined AI evaluations: {combined_file}")
        return pd.read_csv(combined_file)
    elif os.path.exists(random_file):
        print(f"Using random 100 AI evaluations: {random_file}")
        return pd.read_csv(random_file)
    else:
        raise FileNotFoundError("No AI evaluation files found")

def compare_evaluations():
    """Compare human and AI evaluations for overlapping files"""
    # Load data
    human_df = load_human_evaluations('clean_results/false_positive_annotations.jsonl')
    ai_df = load_ai_evaluations()
    
    # Find overlapping files
    overlap_files = set(human_df['filename']) & set(ai_df['file_name'])
    print(f"Found {len(overlap_files)} overlapping files")
    
    # Filter to overlapping files
    human_overlap = human_df[human_df['filename'].isin(overlap_files)].copy()
    ai_overlap = ai_df[ai_df['file_name'].isin(overlap_files)].copy()
    
    # Merge the datasets
    merged = pd.merge(
        human_overlap, 
        ai_overlap, 
        left_on='filename', 
        right_on='file_name',
        how='inner'
    )
    
    print(f"Merged dataset has {len(merged)} rows")
    
    # Convert human decision to binary
    merged['human_false_positive'] = merged['decision'] == 'false_positive'
    
    # For AI evaluator, we need to determine if it found evaluation issues
    # If any issue confidence > 0.5, we consider AI found issues (suggesting false positive)
    issue_cols = ['rephrasing_issues', 'attacker_failure_issues', 'benign_elaboration', 
                  'capability_issues', 'multi_step_issues', 'soft_refusal']
    
    merged['ai_found_issues'] = (merged[issue_cols] > 0.5).any(axis=1)
    
    # Compare decisions
    merged['agreement'] = merged['human_false_positive'] == merged['ai_found_issues']
    
    print("\nComparison Results:")
    print(f"Total comparisons: {len(merged)}")
    print(f"Agreement: {merged['agreement'].sum()} ({merged['agreement'].mean():.2%})")
    print(f"Disagreement: {(~merged['agreement']).sum()} ({(~merged['agreement']).mean():.2%})")
    
    # Confusion matrix
    print("\nConfusion Matrix:")
    print("Human \\ AI     Found Issues    No Issues")
    print(f"False Positive    {((merged['human_false_positive']) & (merged['ai_found_issues'])).sum():8}      {((merged['human_false_positive']) & (~merged['ai_found_issues'])).sum():8}")
    print(f"True Positive     {((~merged['human_false_positive']) & (merged['ai_found_issues'])).sum():8}      {((~merged['human_false_positive']) & (~merged['ai_found_issues'])).sum():8}")
    
    # Save detailed comparison
    comparison_cols = ['filename', 'test_case', 'jailbreak_tactic', 'target_model_x',
                       'decision', 'human_false_positive', 'ai_found_issues', 
                       'agreement'] + issue_cols
    
    merged[comparison_cols].to_csv('human_ai_comparison.csv', index=False)
    print(f"\nDetailed comparison saved to human_ai_comparison.csv")
    
    # Analyze by test case and tactic
    print("\nBy Test Case:")
    test_case_analysis = merged.groupby('test_case').agg({
        'agreement': ['count', 'sum', 'mean'],
        'human_false_positive': 'sum',
        'ai_found_issues': 'sum'
    }).round(3)
    print(test_case_analysis)
    
    print("\nBy Jailbreak Tactic:")
    tactic_analysis = merged.groupby('jailbreak_tactic').agg({
        'agreement': ['count', 'sum', 'mean'],
        'human_false_positive': 'sum',
        'ai_found_issues': 'sum'
    }).round(3)
    print(tactic_analysis)
    
    return merged

def plot_comparison(merged_df):
    """Create visualization of human vs AI comparison"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Agreement rate by test case
    test_case_agreement = merged_df.groupby('test_case')['agreement'].agg(['count', 'mean']).reset_index()
    test_case_agreement = test_case_agreement[test_case_agreement['count'] >= 1]  # Only cases with data
    
    axes[0, 0].bar(range(len(test_case_agreement)), test_case_agreement['mean'])
    axes[0, 0].set_xlabel('Test Case')
    axes[0, 0].set_ylabel('Agreement Rate')
    axes[0, 0].set_title('Human-AI Agreement Rate by Test Case')
    axes[0, 0].set_xticks(range(len(test_case_agreement)))
    axes[0, 0].set_xticklabels(test_case_agreement['test_case'], rotation=45, ha='right')
    axes[0, 0].set_ylim(0, 1)
    
    # Add count labels
    for i, (count, rate) in enumerate(zip(test_case_agreement['count'], test_case_agreement['mean'])):
        axes[0, 0].text(i, rate + 0.02, f'n={count}', ha='center', va='bottom', fontsize=8)
    
    # 2. Confusion matrix as heatmap
    confusion_matrix = pd.crosstab(
        merged_df['human_false_positive'], 
        merged_df['ai_found_issues'], 
        normalize='all'
    )
    
    sns.heatmap(confusion_matrix, annot=True, fmt='.2f', cmap='Blues', ax=axes[0, 1])
    axes[0, 1].set_xlabel('AI Found Issues')
    axes[0, 1].set_ylabel('Human: False Positive')
    axes[0, 1].set_title('Confusion Matrix (Normalized)')
    
    # 3. Issue type detection comparison
    issue_cols = ['rephrasing_issues', 'attacker_failure_issues', 'benign_elaboration', 
                  'capability_issues', 'multi_step_issues', 'soft_refusal']
    
    # For each issue type, compare detection rates between human false positives and true positives
    human_fp = merged_df[merged_df['human_false_positive']]
    human_tp = merged_df[~merged_df['human_false_positive']]
    
    fp_means = human_fp[issue_cols].mean()
    tp_means = human_tp[issue_cols].mean()
    
    x = np.arange(len(issue_cols))
    width = 0.35
    
    axes[1, 0].bar(x - width/2, fp_means, width, label='Human: False Positive', alpha=0.8)
    axes[1, 0].bar(x + width/2, tp_means, width, label='Human: True Positive', alpha=0.8)
    axes[1, 0].set_xlabel('AI Issue Types')
    axes[1, 0].set_ylabel('Mean AI Confidence Score')
    axes[1, 0].set_title('AI Issue Detection by Human Classification')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels([col.replace('_', '\n') for col in issue_cols], rotation=45, ha='right')
    axes[1, 0].legend()
    
    # 4. Overall agreement pie chart
    agreement_counts = merged_df['agreement'].value_counts()
    axes[1, 1].pie(agreement_counts.values, labels=['Disagree', 'Agree'], autopct='%1.1f%%', startangle=90)
    axes[1, 1].set_title(f'Overall Agreement\n(n={len(merged_df)} files)')
    
    plt.tight_layout()
    plt.savefig('human_ai_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    merged_data = compare_evaluations()
    plot_comparison(merged_data) 