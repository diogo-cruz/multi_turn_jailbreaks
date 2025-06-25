#!/usr/bin/env python3
"""
Script to compare original goal_achieved evaluations and AI meta-evaluator results
This is a parallel pipeline to the human vs AI comparison, replacing human evaluations
with original AI evaluations from the conversation data.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import numpy as np
import os
import glob

def load_original_evaluations(batch_dir='clean_results/final_runs/batch3A'):
    """Load original goal_achieved evaluations from JSONL files"""
    original_data = []
    
    # Get all JSONL files from the batch directory
    jsonl_files = glob.glob(f"{batch_dir}/**/*.jsonl", recursive=True)
    
    print(f"Processing {len(jsonl_files)} JSONL files...")
    
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, 'r') as f:
                data = []
                for line in f:
                    if line.strip():
                        data.append(json.loads(line.strip()))
                
                # Extract original goal_achieved evaluation
                goal_achieved = any(entry.get("goal_achieved", False) for entry in data)
                
                # Extract metadata from filename and data
                filename = os.path.basename(jsonl_file)
                
                # Try to extract metadata from the first entry
                if data:
                    first_entry = data[0]
                    original_data.append({
                        'filename': filename,
                        'goal_achieved': goal_achieved,
                        'test_case': first_entry.get('test_case', ''),
                        'jailbreak_tactic': first_entry.get('jailbreak_tactic', ''),
                        'target_model': first_entry.get('target_model', ''),
                        'evaluator_model': first_entry.get('evaluator_model', ''),
                        'turn_type': first_entry.get('turn_type', ''),
                        'full_path': jsonl_file
                    })
                    
        except Exception as e:
            print(f"Error processing {jsonl_file}: {e}")
            continue
    
    return pd.DataFrame(original_data)

def load_ai_evaluations():
    """Load AI meta-evaluations from multiple CSV files and combine them"""
    # Try to load and combine multiple AI meta-evaluation files for maximum coverage
    possible_files = [
        'combined_meta_evaluation_results/issue_scores_combined_20250617_064347.csv',
        'new_cases_meta_evaluation_results/new_cases_scores_20250621_002807.csv',
        'human_overlap_meta_evaluation_results/issue_scores_20250617_064158.csv',
        'random_100_meta_evaluation_results/issue_scores_20250617_005322.csv'
    ]
    
    dfs = []
    for filepath in possible_files:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)} AI meta-evaluations from {filepath}")
            dfs.append(df)
    
    if not dfs:
        raise FileNotFoundError("No AI meta-evaluation files found")
    
    # Combine all dataframes and remove duplicates based on file_name
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['file_name'], keep='first')
    
    print(f"Combined total: {len(combined_df)} unique AI meta-evaluations")
    return combined_df

def load_from_csv_results():
    """Alternative: Load original evaluations from processed CSV files"""
    csv_files = [
        'csv_results/batch3A_results.csv',
        'csv_results/batch3A_complete_fp.csv',
        'csv_results/master_results_verified.csv'
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"Using CSV results: {csv_file}")
            df = pd.read_csv(csv_file)
            
            # Standardize column names
            if 'source_file' in df.columns:
                df['filename'] = df['source_file'].apply(lambda x: os.path.basename(x) if pd.notna(x) else '')
            
            return df[df['batch'] == 'batch3A'] if 'batch' in df.columns else df
    
    raise FileNotFoundError("No CSV result files found")

def compare_evaluations():
    """Compare original goal_achieved and AI meta-evaluations for overlapping files"""
    
    # Load human evaluations to get the exact set of files we should focus on
    # Use the comprehensive human evaluation dataset that matches the human vs AI comparison
    try:
        human_df = pd.read_csv('final_comprehensive_human_ai_comparison.csv')
        human_filenames = set(human_df['filename'].apply(lambda x: os.path.basename(x).replace('.jsonl', '')))
        print(f"Loaded {len(human_filenames)} human-evaluated filenames as reference (comprehensive)")
    except Exception as e:
        print(f"Could not load comprehensive human evaluations, trying smaller dataset: {e}")
        try:
            human_df = pd.read_json('clean_results/false_positive_annotations.jsonl', lines=True)
            human_filenames = set(human_df['filename'].apply(lambda x: os.path.basename(x).replace('.jsonl', '')))
            print(f"Loaded {len(human_filenames)} human-evaluated filenames as reference (smaller)")
        except Exception as e2:
            print(f"Could not load any human evaluations: {e2}")
            human_filenames = set()
    
    # Load AI meta-evaluations (which contains both original and AI evaluations)
    ai_df = load_ai_evaluations()
    print(f"Loaded {len(ai_df)} AI meta-evaluations")
    
    # The AI meta-evaluation file should contain original_goal_achieved
    if 'original_goal_achieved' not in ai_df.columns:
        print("Error: original_goal_achieved column not found in AI meta-evaluation data")
        return None
    
    # Find overlapping files by matching filename patterns
    def normalize_filename(filename):
        """Normalize filename for matching"""
        if pd.isna(filename):
            return ''
        # Remove .jsonl extension and any path components
        base = os.path.basename(str(filename)).replace('.jsonl', '')
        return base
    
    ai_df['normalized_filename'] = ai_df['file_name'].apply(normalize_filename)
    
    # Filter to files that were human-evaluated (to match scope of human vs AI comparison)
    if human_filenames:
        overlap_files = set(ai_df['normalized_filename']) & human_filenames
        ai_overlap = ai_df[ai_df['normalized_filename'].isin(overlap_files)].copy()
        print(f"Found {len(ai_overlap)} overlapping files (filtered to human-evaluated subset)")
    else:
        ai_overlap = ai_df.copy()
        print(f"Using all {len(ai_overlap)} AI meta-evaluation files")
    
    if len(ai_overlap) == 0:
        print("No overlapping files found. Checking filename patterns...")
        print("Sample AI filenames:", ai_df['normalized_filename'].head().tolist())
        if human_filenames:
            print("Sample human filenames:", list(human_filenames)[:5])
        return None
    
    # Prepare the merged dataset
    merged = ai_overlap.copy()
    
    print(f"Merged dataset has {len(merged)} rows")
    
    # Convert original goal_achieved to binary (should already be boolean)
    merged['original_goal_achieved'] = merged['original_goal_achieved'].astype(bool)
    
    # For AI meta-evaluator, determine if it found evaluation issues
    # If any issue confidence > 0.5, we consider AI found issues (suggesting original evaluation was wrong)
    issue_cols = ['rephrasing_issues', 'attacker_failure_issues', 'benign_elaboration', 
                  'capability_issues', 'multi_step_issues', 'soft_refusal']
    
    # Check which columns actually exist
    existing_issue_cols = [col for col in issue_cols if col in merged.columns]
    if not existing_issue_cols:
        print("Warning: No standard issue columns found. Available columns:")
        print([col for col in merged.columns if 'issue' in col.lower() or 'score' in col.lower()])
        # Use any available issue/score columns
        existing_issue_cols = [col for col in merged.columns if 'issue' in col.lower() or col.endswith('_score')]
    
    if existing_issue_cols:
        merged['ai_found_issues'] = (merged[existing_issue_cols] > 0.5).any(axis=1)
    else:
        # Fallback: use any boolean column that might indicate issues
        bool_cols = merged.select_dtypes(include=[bool]).columns
        if len(bool_cols) > 0:
            merged['ai_found_issues'] = merged[bool_cols].any(axis=1)
        else:
            print("Error: Cannot determine AI issue detection method")
            return merged
    
    # Compare decisions
    # Agreement means: original said goal_achieved=True AND AI found no issues, 
    # OR original said goal_achieved=False AND AI found issues
    merged['agreement'] = merged['original_goal_achieved'] == (~merged['ai_found_issues'])
    
    print("\nComparison Results:")
    print(f"Total comparisons: {len(merged)}")
    print(f"Agreement: {merged['agreement'].sum()} ({merged['agreement'].mean():.2%})")
    print(f"Disagreement: {(~merged['agreement']).sum()} ({(~merged['agreement']).mean():.2%})")
    
    # Detailed breakdown
    print(f"\nOriginal Evaluations:")
    print(f"Goal Achieved (True): {merged['original_goal_achieved'].sum()} ({merged['original_goal_achieved'].mean():.2%})")
    print(f"Goal Not Achieved (False): {(~merged['original_goal_achieved']).sum()} ({(~merged['original_goal_achieved']).mean():.2%})")
    
    print(f"\nAI Meta-Evaluations:")
    print(f"Found Issues: {merged['ai_found_issues'].sum()} ({merged['ai_found_issues'].mean():.2%})")
    print(f"No Issues Found: {(~merged['ai_found_issues']).sum()} ({(~merged['ai_found_issues']).mean():.2%})")
    
    # Confusion matrix
    print("\nConfusion Matrix:")
    print("Original \\ AI Meta    Found Issues    No Issues")
    print(f"Goal Achieved       {((merged['original_goal_achieved']) & (merged['ai_found_issues'])).sum():8}      {((merged['original_goal_achieved']) & (~merged['ai_found_issues'])).sum():8}")
    print(f"Goal Not Achieved   {((~merged['original_goal_achieved']) & (merged['ai_found_issues'])).sum():8}      {((~merged['original_goal_achieved']) & (~merged['ai_found_issues'])).sum():8}")
    
    # Save detailed comparison
    comparison_cols = ['file_name', 'tactic', 'target_model',
                       'original_goal_achieved', 'ai_found_issues', 'agreement'] + existing_issue_cols
    
    # Only include columns that exist
    comparison_cols = [col for col in comparison_cols if col in merged.columns]
    
    merged[comparison_cols].to_csv('original_ai_comparison.csv', index=False)
    print(f"\nDetailed comparison saved to original_ai_comparison.csv")
    
    # Analyze by test case and tactic if these columns exist
    # Note: test_case might not be in the AI meta-evaluation file, so we'll skip if not available
    if 'tactic' in merged.columns:
        print("\nBy Jailbreak Tactic:")
        tactic_analysis = merged.groupby('tactic').agg({
            'agreement': ['count', 'sum', 'mean'],
            'original_goal_achieved': 'sum',
            'ai_found_issues': 'sum'
        }).round(3)
        print(tactic_analysis)
    
    return merged

def plot_comparison(merged_df):
    """Create visualization of original vs AI meta-evaluation comparison"""
    if merged_df is None or len(merged_df) == 0:
        print("No data to plot")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Agreement rate by test case
    if 'test_case_original' in merged_df.columns:
        test_case_agreement = merged_df.groupby('test_case_original')['agreement'].agg(['count', 'mean']).reset_index()
        test_case_agreement = test_case_agreement[test_case_agreement['count'] >= 1]
        
        if len(test_case_agreement) > 0:
            axes[0, 0].bar(range(len(test_case_agreement)), test_case_agreement['mean'])
            axes[0, 0].set_xlabel('Test Case')
            axes[0, 0].set_ylabel('Agreement Rate')
            axes[0, 0].set_title('Original-AI Meta Agreement Rate by Test Case')
            axes[0, 0].set_xticks(range(len(test_case_agreement)))
            axes[0, 0].set_xticklabels(test_case_agreement['test_case_original'], rotation=45, ha='right')
            axes[0, 0].set_ylim(0, 1)
            
            # Add count labels
            for i, (count, rate) in enumerate(zip(test_case_agreement['count'], test_case_agreement['mean'])):
                axes[0, 0].text(i, rate + 0.02, f'n={count}', ha='center', va='bottom', fontsize=8)
    else:
        axes[0, 0].text(0.5, 0.5, 'Test case data not available', ha='center', va='center', transform=axes[0, 0].transAxes)
        axes[0, 0].set_title('Agreement Rate by Test Case')
    
    # 2. Confusion matrix as heatmap
    confusion_matrix = pd.crosstab(
        merged_df['original_goal_achieved'], 
        merged_df['ai_found_issues'], 
        normalize='all'
    )
    
    sns.heatmap(confusion_matrix, annot=True, fmt='.2f', cmap='Blues', ax=axes[0, 1])
    axes[0, 1].set_xlabel('AI Meta: Found Issues')
    axes[0, 1].set_ylabel('Original: Goal Achieved')
    axes[0, 1].set_title('Confusion Matrix (Normalized)')
    
    # 3. Issue type detection comparison
    issue_cols = [col for col in merged_df.columns if 'issue' in col.lower() and merged_df[col].dtype in ['float64', 'int64']]
    
    if len(issue_cols) > 0:
        # Compare issue detection rates between original goal achieved vs not achieved
        goal_achieved = merged_df[merged_df['original_goal_achieved']]
        goal_not_achieved = merged_df[~merged_df['original_goal_achieved']]
        
        achieved_means = goal_achieved[issue_cols].mean()
        not_achieved_means = goal_not_achieved[issue_cols].mean()
        
        x = np.arange(len(issue_cols))
        width = 0.35
        
        axes[1, 0].bar(x - width/2, achieved_means, width, label='Original: Goal Achieved', alpha=0.8)
        axes[1, 0].bar(x + width/2, not_achieved_means, width, label='Original: Goal Not Achieved', alpha=0.8)
        axes[1, 0].set_xlabel('AI Meta Issue Types')
        axes[1, 0].set_ylabel('Mean AI Confidence Score')
        axes[1, 0].set_title('AI Meta Issue Detection by Original Goal Status')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels([col.replace('_', '\n') for col in issue_cols], rotation=45, ha='right')
        axes[1, 0].legend()
    else:
        axes[1, 0].text(0.5, 0.5, 'Issue score data not available', ha='center', va='center', transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('AI Meta Issue Detection by Original Goal Status')
    
    # 4. Overall agreement pie chart
    agreement_counts = merged_df['agreement'].value_counts()
    labels = ['Disagree', 'Agree'] if False in agreement_counts.index else ['Agree']
    values = [agreement_counts.get(False, 0), agreement_counts.get(True, 0)] if False in agreement_counts.index else [agreement_counts.get(True, 0)]
    
    axes[1, 1].pie([v for v in values if v > 0], labels=[l for l, v in zip(labels, values) if v > 0], autopct='%1.1f%%', startangle=90)
    axes[1, 1].set_title(f'Overall Agreement\n(n={len(merged_df)} files)')
    
    plt.tight_layout()
    plt.savefig('original_ai_comparison.png', dpi=300, bbox_inches='tight')
    print("Plot saved as original_ai_comparison.png")
    plt.show()

if __name__ == "__main__":
    merged_data = compare_evaluations()
    if merged_data is not None:
        plot_comparison(merged_data)