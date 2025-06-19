#!/usr/bin/env python3
"""
Meta-Evaluation Results Analysis and Plotting

This script analyzes the meta-evaluation results to identify false positives and false negatives
in the original evaluation system, creating visualizations by tactic, test case, and turn type.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import json
from pathlib import Path

def load_meta_evaluation_data():
    """Load the meta-evaluation CSV data."""
    # First try to find combined results, then fall back to random 100 results
    combined_dir = "combined_meta_evaluation_results"
    random_dir = "random_100_meta_evaluation_results"
    
    # Check for combined results first
    if os.path.exists(combined_dir):
        csv_files = list(Path(combined_dir).glob("issue_scores_combined_*.csv"))
        if csv_files:
            csv_file = max(csv_files, key=os.path.getctime)
            print(f"Loading COMBINED data from: {csv_file}")
            df = pd.read_csv(csv_file)
            return df
    
    # Fall back to random 100 results
    if not os.path.exists(random_dir):
        raise FileNotFoundError(f"No meta-evaluation results found. Checked: {combined_dir}, {random_dir}")
    
    csv_files = list(Path(random_dir).glob("issue_scores_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {random_dir}")
    
    # Use the most recent file
    csv_file = max(csv_files, key=os.path.getctime)
    print(f"Loading data from: {csv_file}")
    
    df = pd.read_csv(csv_file)
    return df

def extract_metadata(df):
    """Extract additional metadata from filenames and prepare data for analysis."""
    # Extract turn type from filename
    df['turn_type'] = df['file_name'].apply(
        lambda x: 'multi_turn' if 'multi_turn' in x else 'single_turn'
    )
    
    # Extract test case from filename (the part after tactic and before model)
    def extract_test_case(filename):
        parts = filename.split('_')
        # Find the tactic part and skip it
        if 'direct_request' in filename:
            start_idx = 2  # Skip 'direct', 'request'
        elif 'emotional_appeal' in filename:
            start_idx = 2  # Skip 'emotional', 'appeal'
        else:
            start_idx = 1  # Skip single word tactics like 'crowding', 'command'
        
        # Find where the model name starts (usually contains 'gpt', 'claude', 'gemini', 'deepseek')
        model_indicators = ['gpt', 'claude', 'gemini', 'deepseek']
        end_idx = len(parts)
        for i, part in enumerate(parts[start_idx:], start_idx):
            if any(indicator in part.lower() for indicator in model_indicators):
                end_idx = i
                break
        
        return '_'.join(parts[start_idx:end_idx])
    
    df['test_case'] = df['file_name'].apply(extract_test_case)
    
    # Calculate false positives and false negatives
    df['false_positive'] = (df['original_goal_achieved'] == True) & (df['corrected_goal_achieved'] == False)
    df['false_negative'] = (df['original_goal_achieved'] == False) & (df['corrected_goal_achieved'] == True)
    df['correct_evaluation'] = df['original_goal_achieved'] == df['corrected_goal_achieved']
    
    return df

def create_tactic_analysis_plots(df, output_dir):
    """Create plots analyzing false positives/negatives by tactic."""
    
    # Calculate rates by tactic and turn type
    tactic_analysis = df.groupby(['tactic', 'turn_type']).agg({
        'false_positive': ['count', 'sum'],
        'false_negative': ['count', 'sum'],
        'correct_evaluation': 'sum'
    }).reset_index()
    
    # Flatten column names
    tactic_analysis.columns = ['tactic', 'turn_type', 'total_count', 'fp_count', 'total_count2', 'fn_count', 'correct_count']
    tactic_analysis['fp_rate'] = tactic_analysis['fp_count'] / tactic_analysis['total_count']
    tactic_analysis['fn_rate'] = tactic_analysis['fn_count'] / tactic_analysis['total_count']
    tactic_analysis['accuracy'] = tactic_analysis['correct_count'] / tactic_analysis['total_count']
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Evaluation Accuracy by Jailbreak Tactic and Turn Type', fontsize=16, fontweight='bold')
    
    # False Positive Rate by Tactic
    pivot_fp = tactic_analysis.pivot(index='tactic', columns='turn_type', values='fp_rate')
    sns.heatmap(pivot_fp, annot=True, fmt='.3f', cmap='Reds', ax=axes[0,0], 
                cbar_kws={'label': 'False Positive Rate'})
    axes[0,0].set_title('False Positive Rate by Tactic')
    axes[0,0].set_xlabel('Turn Type')
    axes[0,0].set_ylabel('Jailbreak Tactic')
    
    # False Negative Rate by Tactic
    pivot_fn = tactic_analysis.pivot(index='tactic', columns='turn_type', values='fn_rate')
    sns.heatmap(pivot_fn, annot=True, fmt='.3f', cmap='Blues', ax=axes[0,1],
                cbar_kws={'label': 'False Negative Rate'})
    axes[0,1].set_title('False Negative Rate by Tactic')
    axes[0,1].set_xlabel('Turn Type')
    axes[0,1].set_ylabel('Jailbreak Tactic')
    
    # Overall Accuracy by Tactic
    pivot_acc = tactic_analysis.pivot(index='tactic', columns='turn_type', values='accuracy')
    sns.heatmap(pivot_acc, annot=True, fmt='.3f', cmap='Greens', ax=axes[1,0],
                cbar_kws={'label': 'Accuracy'})
    axes[1,0].set_title('Evaluation Accuracy by Tactic')
    axes[1,0].set_xlabel('Turn Type')
    axes[1,0].set_ylabel('Jailbreak Tactic')
    
    # Sample counts by tactic
    pivot_count = tactic_analysis.pivot(index='tactic', columns='turn_type', values='total_count')
    sns.heatmap(pivot_count, annot=True, fmt='d', cmap='Purples', ax=axes[1,1],
                cbar_kws={'label': 'Sample Count'})
    axes[1,1].set_title('Sample Counts by Tactic')
    axes[1,1].set_xlabel('Turn Type')
    axes[1,1].set_ylabel('Jailbreak Tactic')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'tactic_analysis_heatmaps.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return tactic_analysis

def create_test_case_analysis_plots(df, output_dir):
    """Create plots analyzing false positives/negatives by test case."""
    
    # Calculate rates by test case and turn type
    test_case_analysis = df.groupby(['test_case', 'turn_type']).agg({
        'false_positive': ['count', 'sum'],
        'false_negative': ['count', 'sum'],
        'correct_evaluation': 'sum'
    }).reset_index()
    
    # Flatten column names
    test_case_analysis.columns = ['test_case', 'turn_type', 'total_count', 'fp_count', 'total_count2', 'fn_count', 'correct_count']
    test_case_analysis['fp_rate'] = test_case_analysis['fp_count'] / test_case_analysis['total_count']
    test_case_analysis['fn_rate'] = test_case_analysis['fn_count'] / test_case_analysis['total_count']
    test_case_analysis['accuracy'] = test_case_analysis['correct_count'] / test_case_analysis['total_count']
    
    # Get top test cases by sample count for readability
    top_test_cases = df['test_case'].value_counts().head(15).index.tolist()
    filtered_analysis = test_case_analysis[test_case_analysis['test_case'].isin(top_test_cases)]
    
    # Create bar plots
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle('Evaluation Accuracy by Test Case (Top 15 by Sample Count)', fontsize=16, fontweight='bold')
    
    # False Positive Rate by Test Case
    fp_data = filtered_analysis.pivot(index='test_case', columns='turn_type', values='fp_rate').fillna(0)
    fp_data.plot(kind='bar', ax=axes[0,0], color=['red', 'darkred'], alpha=0.7)
    axes[0,0].set_title('False Positive Rate by Test Case')
    axes[0,0].set_xlabel('Test Case')
    axes[0,0].set_ylabel('False Positive Rate')
    axes[0,0].legend(title='Turn Type')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # False Negative Rate by Test Case
    fn_data = filtered_analysis.pivot(index='test_case', columns='turn_type', values='fn_rate').fillna(0)
    fn_data.plot(kind='bar', ax=axes[0,1], color=['blue', 'darkblue'], alpha=0.7)
    axes[0,1].set_title('False Negative Rate by Test Case')
    axes[0,1].set_xlabel('Test Case')
    axes[0,1].set_ylabel('False Negative Rate')
    axes[0,1].legend(title='Turn Type')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # Accuracy by Test Case
    acc_data = filtered_analysis.pivot(index='test_case', columns='turn_type', values='accuracy').fillna(0)
    acc_data.plot(kind='bar', ax=axes[1,0], color=['green', 'darkgreen'], alpha=0.7)
    axes[1,0].set_title('Evaluation Accuracy by Test Case')
    axes[1,0].set_xlabel('Test Case')
    axes[1,0].set_ylabel('Accuracy')
    axes[1,0].legend(title='Turn Type')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # Sample counts by test case
    count_data = filtered_analysis.pivot(index='test_case', columns='turn_type', values='total_count').fillna(0)
    count_data.plot(kind='bar', ax=axes[1,1], color=['purple', 'darkviolet'], alpha=0.7)
    axes[1,1].set_title('Sample Counts by Test Case')
    axes[1,1].set_xlabel('Test Case')
    axes[1,1].set_ylabel('Sample Count')
    axes[1,1].legend(title='Turn Type')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'test_case_analysis_bars.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return test_case_analysis

def create_overall_summary_plots(df, output_dir):
    """Create overall summary plots."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Meta-Evaluation Summary: Original vs Corrected Evaluations', fontsize=16, fontweight='bold')
    
    # Overall false positive/negative rates
    overall_fp_rate = df['false_positive'].mean()
    overall_fn_rate = df['false_negative'].mean()
    overall_accuracy = df['correct_evaluation'].mean()
    
    # Pie chart of evaluation outcomes
    labels = ['Correct Evaluations', 'False Positives', 'False Negatives']
    sizes = [overall_accuracy, overall_fp_rate, overall_fn_rate]
    colors = ['green', 'red', 'blue']
    
    axes[0,0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    axes[0,0].set_title('Overall Evaluation Accuracy')
    
    # Turn type comparison
    turn_summary = df.groupby('turn_type').agg({
        'false_positive': 'mean',
        'false_negative': 'mean',
        'correct_evaluation': 'mean'
    })
    
    turn_summary[['false_positive', 'false_negative']].plot(kind='bar', ax=axes[0,1], 
                                                           color=['red', 'blue'], alpha=0.7)
    axes[0,1].set_title('Error Rates by Turn Type')
    axes[0,1].set_xlabel('Turn Type')
    axes[0,1].set_ylabel('Error Rate')
    axes[0,1].legend(['False Positive', 'False Negative'])
    axes[0,1].tick_params(axis='x', rotation=0)
    
    # Confusion matrix
    confusion_data = pd.crosstab(df['original_goal_achieved'], df['corrected_goal_achieved'], 
                                margins=True, normalize='index')
    sns.heatmap(confusion_data.iloc[:-1, :-1], annot=True, fmt='.3f', cmap='Blues', ax=axes[1,0])
    axes[1,0].set_title('Confusion Matrix (Normalized by Original Evaluation)')
    axes[1,0].set_xlabel('Corrected Goal Achieved')
    axes[1,0].set_ylabel('Original Goal Achieved')
    
    # Issue type prevalence
    issue_cols = ['capability_issues', 'multi_step_issues', 'rephrasing_issues', 
                  'attacker_failure_issues', 'soft_refusal', 'benign_elaboration']
    
    # Count high confidence issues (>= 0.8)
    issue_counts = {}
    for col in issue_cols:
        if col in df.columns:
            issue_counts[col.replace('_', ' ').title()] = (df[col] >= 0.8).sum()
    
    if issue_counts:
        axes[1,1].bar(range(len(issue_counts)), list(issue_counts.values()), alpha=0.7)
        axes[1,1].set_title('High-Confidence Issue Detection')
        axes[1,1].set_xlabel('Issue Type')
        axes[1,1].set_ylabel('Count')
        axes[1,1].set_xticks(range(len(issue_counts)))
        axes[1,1].set_xticklabels(list(issue_counts.keys()), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'overall_summary.png'), dpi=300, bbox_inches='tight')
    plt.close()

def create_model_comparison_plots(df, output_dir):
    """Create plots comparing performance across target models."""
    
    # Calculate rates by model
    model_analysis = df.groupby(['target_model', 'turn_type']).agg({
        'false_positive': ['count', 'sum'],
        'false_negative': ['count', 'sum'],
        'correct_evaluation': 'sum'
    }).reset_index()
    
    # Flatten column names
    model_analysis.columns = ['target_model', 'turn_type', 'total_count', 'fp_count', 'total_count2', 'fn_count', 'correct_count']
    model_analysis['fp_rate'] = model_analysis['fp_count'] / model_analysis['total_count']
    model_analysis['fn_rate'] = model_analysis['fn_count'] / model_analysis['total_count']
    model_analysis['accuracy'] = model_analysis['correct_count'] / model_analysis['total_count']
    
    # Clean model names for readability
    model_analysis['model_short'] = model_analysis['target_model'].apply(
        lambda x: x.split('/')[-1] if '/' in x else x
    )
    
    # Filter to models with enough samples
    model_counts = model_analysis.groupby('model_short')['total_count'].sum()
    models_with_samples = model_counts[model_counts >= 3].index.tolist()
    filtered_model_analysis = model_analysis[model_analysis['model_short'].isin(models_with_samples)]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Evaluation Accuracy by Target Model', fontsize=16, fontweight='bold')
    
    # False Positive Rate by Model
    fp_pivot = filtered_model_analysis.pivot(index='model_short', columns='turn_type', values='fp_rate').fillna(0)
    fp_pivot.plot(kind='bar', ax=axes[0,0], color=['red', 'darkred'], alpha=0.7)
    axes[0,0].set_title('False Positive Rate by Model')
    axes[0,0].set_xlabel('Target Model')
    axes[0,0].set_ylabel('False Positive Rate')
    axes[0,0].legend(title='Turn Type')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # False Negative Rate by Model
    fn_pivot = filtered_model_analysis.pivot(index='model_short', columns='turn_type', values='fn_rate').fillna(0)
    fn_pivot.plot(kind='bar', ax=axes[0,1], color=['blue', 'darkblue'], alpha=0.7)
    axes[0,1].set_title('False Negative Rate by Model')
    axes[0,1].set_xlabel('Target Model')
    axes[0,1].set_ylabel('False Negative Rate')
    axes[0,1].legend(title='Turn Type')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    # Accuracy by Model
    acc_pivot = filtered_model_analysis.pivot(index='model_short', columns='turn_type', values='accuracy').fillna(0)
    acc_pivot.plot(kind='bar', ax=axes[1,0], color=['green', 'darkgreen'], alpha=0.7)
    axes[1,0].set_title('Evaluation Accuracy by Model')
    axes[1,0].set_xlabel('Target Model')
    axes[1,0].set_ylabel('Accuracy')
    axes[1,0].legend(title='Turn Type')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # Sample counts by model
    count_pivot = filtered_model_analysis.pivot(index='model_short', columns='turn_type', values='total_count').fillna(0)
    count_pivot.plot(kind='bar', ax=axes[1,1], color=['purple', 'darkviolet'], alpha=0.7)
    axes[1,1].set_title('Sample Counts by Model')
    axes[1,1].set_xlabel('Target Model')
    axes[1,1].set_ylabel('Sample Count')
    axes[1,1].legend(title='Turn Type')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'model_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    return filtered_model_analysis

def load_human_evaluations(filepath):
    """Load human evaluations from JSONL file"""
    human_data = []
    with open(filepath, 'r') as f:
        for line in f:
            human_data.append(json.loads(line.strip()))
    return pd.DataFrame(human_data)

def create_human_ai_comparison_plots(df, output_dir):
    """Create plots comparing human and AI meta-evaluator results."""
    
    # Check if human evaluation file exists
    human_file = 'clean_results/false_positive_annotations.jsonl'
    if not os.path.exists(human_file):
        print(f"Human evaluation file not found: {human_file}")
        print("Skipping human vs AI comparison plots.")
        return None
    
    try:
        # Load human evaluations
        human_df = load_human_evaluations(human_file)
        
        # Find overlapping files
        overlap_files = set(human_df['filename']) & set(df['file_name'])
        
        if len(overlap_files) == 0:
            print("No overlapping files found between human and AI evaluations.")
            print("Skipping human vs AI comparison plots.")
            return None
        
        print(f"Found {len(overlap_files)} overlapping files for human vs AI comparison")
        
        # Filter to overlapping files
        human_overlap = human_df[human_df['filename'].isin(overlap_files)].copy()
        ai_overlap = df[df['file_name'].isin(overlap_files)].copy()
        
        # Merge the datasets
        merged = pd.merge(
            human_overlap, 
            ai_overlap, 
            left_on='filename', 
            right_on='file_name',
            how='inner'
        )
        
        # Convert human decision to binary
        merged['human_false_positive'] = merged['decision'] == 'false_positive'
        
        # For AI evaluator, determine if it found evaluation issues
        # If any issue confidence > 0.5, we consider AI found issues (suggesting false positive)
        issue_cols = ['rephrasing_issues', 'attacker_failure_issues', 'benign_elaboration', 
                      'capability_issues', 'multi_step_issues', 'soft_refusal']
        
        merged['ai_found_issues'] = (merged[issue_cols] > 0.5).any(axis=1)
        
        # Compare decisions
        merged['agreement'] = merged['human_false_positive'] == merged['ai_found_issues']
        
        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Human vs AI Meta-Evaluator Comparison', fontsize=16, fontweight='bold')
        
        # 1. Agreement rate by test case
        if len(merged) > 0:
            # Use the test_case column from human data (test_case_x after merge)  
            test_case_col = 'test_case_x' if 'test_case_x' in merged.columns else 'test_case'
            test_case_agreement = merged.groupby(test_case_col)['agreement'].agg(['count', 'mean']).reset_index()
            test_case_agreement = test_case_agreement[test_case_agreement['count'] >= 1]
            
            if len(test_case_agreement) > 0:
                axes[0, 0].bar(range(len(test_case_agreement)), test_case_agreement['mean'])
                axes[0, 0].set_xlabel('Test Case')
                axes[0, 0].set_ylabel('Agreement Rate')
                axes[0, 0].set_title('Human-AI Agreement Rate by Test Case')
                axes[0, 0].set_xticks(range(len(test_case_agreement)))
                axes[0, 0].set_xticklabels(test_case_agreement[test_case_col], rotation=45, ha='right')
                axes[0, 0].set_ylim(0, 1)
                
                # Add count labels
                for i, (count, rate) in enumerate(zip(test_case_agreement['count'], test_case_agreement['mean'])):
                    axes[0, 0].text(i, rate + 0.02, f'n={count}', ha='center', va='bottom', fontsize=8)
            
            # 2. Confusion matrix as heatmap
            confusion_data = pd.crosstab(
                merged['human_false_positive'], 
                merged['ai_found_issues'], 
                normalize='all'
            )
            
            sns.heatmap(confusion_data, annot=True, fmt='.2f', cmap='Blues', ax=axes[0, 1])
            axes[0, 1].set_xlabel('AI Found Issues')
            axes[0, 1].set_ylabel('Human: False Positive')
            axes[0, 1].set_title('Confusion Matrix (Normalized)')
            
            # 3. Issue type detection comparison
            human_fp = merged[merged['human_false_positive']]
            human_tp = merged[~merged['human_false_positive']]
            
            if len(human_fp) > 0 and len(human_tp) > 0:
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
            elif len(human_fp) > 0:
                fp_means = human_fp[issue_cols].mean()
                axes[1, 0].bar(range(len(issue_cols)), fp_means, label='Human: False Positive', alpha=0.8)
                axes[1, 0].set_xlabel('AI Issue Types')
                axes[1, 0].set_ylabel('Mean AI Confidence Score')
                axes[1, 0].set_title('AI Issue Detection (Human False Positives Only)')
                axes[1, 0].set_xticks(range(len(issue_cols)))
                axes[1, 0].set_xticklabels([col.replace('_', '\n') for col in issue_cols], rotation=45, ha='right')
                axes[1, 0].legend()
            
            # 4. Overall agreement pie chart
            agreement_counts = merged['agreement'].value_counts()
            labels = ['Disagree', 'Agree'] if False in agreement_counts.index else ['Agree']
            values = [agreement_counts.get(False, 0), agreement_counts.get(True, 0)] if False in agreement_counts.index else [agreement_counts.get(True, 0)]
            
            axes[1, 1].pie([v for v in values if v > 0], 
                          labels=[l for l, v in zip(labels, values) if v > 0], 
                          autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title(f'Overall Agreement\n(n={len(merged)} files)')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'human_ai_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Print comparison summary
        print("\n" + "="*50)
        print("HUMAN vs AI META-EVALUATOR COMPARISON")
        print("="*50)
        print(f"Total overlapping files: {len(merged)}")
        print(f"Agreement: {merged['agreement'].sum()} ({merged['agreement'].mean():.1%})")
        print(f"Disagreement: {(~merged['agreement']).sum()} ({(~merged['agreement']).mean():.1%})")
        
        print("\nConfusion Matrix:")
        print("Human \\ AI     Found Issues    No Issues")
        print(f"False Positive    {((merged['human_false_positive']) & (merged['ai_found_issues'])).sum():8}      {((merged['human_false_positive']) & (~merged['ai_found_issues'])).sum():8}")
        print(f"True Positive     {((~merged['human_false_positive']) & (merged['ai_found_issues'])).sum():8}      {((~merged['human_false_positive']) & (~merged['ai_found_issues'])).sum():8}")
        
        return merged
        
    except Exception as e:
        print(f"Error in human vs AI comparison: {e}")
        return None

def print_detailed_analysis(df, tactic_analysis, test_case_analysis):
    """Print detailed analysis findings."""
    
    print("\n" + "="*60)
    print("DETAILED META-EVALUATION ANALYSIS")
    print("="*60)
    
    # Overall statistics
    total_files = len(df)
    fp_count = df['false_positive'].sum()
    fn_count = df['false_negative'].sum()
    correct_count = df['correct_evaluation'].sum()
    
    print(f"\nOVERALL STATISTICS:")
    print(f"Total files analyzed: {total_files}")
    print(f"False positives: {fp_count} ({fp_count/total_files*100:.1f}%)")
    print(f"False negatives: {fn_count} ({fn_count/total_files*100:.1f}%)")
    print(f"Correct evaluations: {correct_count} ({correct_count/total_files*100:.1f}%)")
    
    # Worst performing tactics
    print(f"\nTACTIC ANALYSIS:")
    worst_tactics_fp = tactic_analysis.groupby('tactic')['fp_rate'].mean().sort_values(ascending=False)
    worst_tactics_fn = tactic_analysis.groupby('tactic')['fn_rate'].mean().sort_values(ascending=False)
    
    print("Highest false positive rates by tactic:")
    for tactic, rate in worst_tactics_fp.head(3).items():
        print(f"  {tactic}: {rate:.3f}")
    
    print("Highest false negative rates by tactic:")
    for tactic, rate in worst_tactics_fn.head(3).items():
        print(f"  {tactic}: {rate:.3f}")
    
    # Turn type differences
    print(f"\nTURN TYPE COMPARISON:")
    turn_stats = df.groupby('turn_type')[['false_positive', 'false_negative', 'correct_evaluation']].mean()
    for turn_type in ['single_turn', 'multi_turn']:
        if turn_type in turn_stats.index:
            stats = turn_stats.loc[turn_type]
            print(f"{turn_type}: FP={stats['false_positive']:.3f}, FN={stats['false_negative']:.3f}, Acc={stats['correct_evaluation']:.3f}")
    
    # Issue type correlation
    print(f"\nISSUE TYPE CORRELATION WITH FALSE POSITIVES:")
    issue_cols = ['rephrasing_issues', 'attacker_failure_issues', 'benign_elaboration', 
                  'capability_issues', 'multi_step_issues', 'soft_refusal']
    
    fp_cases = df[df['false_positive'] == True]
    for col in issue_cols:
        if col in df.columns:
            high_conf_count = (fp_cases[col] >= 0.8).sum()
            print(f"  {col}: {high_conf_count}/{len(fp_cases)} ({high_conf_count/len(fp_cases)*100:.1f}%) FP cases have high confidence")

def main():
    """Main analysis function."""
    print("Meta-Evaluation Results Analysis")
    print("="*40)
    
    # Create output directory
    output_dir = "meta_evaluation_plots"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load and prepare data
        df = load_meta_evaluation_data()
        df = extract_metadata(df)
        
        print(f"Loaded {len(df)} files for analysis")
        print(f"Data columns: {list(df.columns)}")
        
        # Create analysis plots
        print("\nGenerating tactic analysis plots...")
        tactic_analysis = create_tactic_analysis_plots(df, output_dir)
        
        print("Generating test case analysis plots...")
        test_case_analysis = create_test_case_analysis_plots(df, output_dir)
        
        print("Generating overall summary plots...")
        create_overall_summary_plots(df, output_dir)
        
        print("Generating model comparison plots...")
        model_analysis = create_model_comparison_plots(df, output_dir)
        
        print("Generating human vs AI comparison plots...")
        human_ai_comparison = create_human_ai_comparison_plots(df, output_dir)
        
        # Print detailed analysis
        print_detailed_analysis(df, tactic_analysis, test_case_analysis)
        
        print(f"\n✅ Analysis complete! Plots saved to: {output_dir}/")
        print("Generated files:")
        for file in os.listdir(output_dir):
            if file.endswith('.png'):
                print(f"  - {file}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 