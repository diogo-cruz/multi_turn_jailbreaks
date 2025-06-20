#!/usr/bin/env python3
"""
Analyze the main sources of disagreement between human and AI meta-evaluators.
This script will test excluding each issue type individually to see which one
most improves agreement between human and AI assessments.
"""

import pandas as pd
import numpy as np
import os

def load_human_evaluations(filepath):
    """Load human evaluation data from JSONL file."""
    import json
    
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            data.append({
                'filename': entry['filename'],
                'decision': entry['decision'],
                'test_case': entry.get('test_case', ''),
                'tactic': entry.get('tactic', '')
            })
    
    return pd.DataFrame(data)

def analyze_disagreement_sources():
    """Analyze which AI issue types are the main sources of disagreement with humans."""
    
    # Load AI meta-evaluation results
    ai_file = 'combined_meta_evaluation_results/issue_scores_combined_20250617_064347.csv'
    if not os.path.exists(ai_file):
        print(f"AI evaluation file not found: {ai_file}")
        return None
    
    ai_df = pd.read_csv(ai_file)
    
    # Load human evaluations
    human_file = 'clean_results/false_positive_annotations.jsonl'
    if not os.path.exists(human_file):
        print(f"Human evaluation file not found: {human_file}")
        return None
    
    human_df = load_human_evaluations(human_file)
    
    # Find overlapping files
    overlap_files = set(human_df['filename']) & set(ai_df['file_name'])
    print(f"Found {len(overlap_files)} overlapping files for analysis")
    
    if len(overlap_files) == 0:
        print("No overlapping files found.")
        return None
    
    # Filter to overlapping files and merge
    human_overlap = human_df[human_df['filename'].isin(overlap_files)].copy()
    ai_overlap = ai_df[ai_df['file_name'].isin(overlap_files)].copy()
    
    merged = pd.merge(
        human_overlap, 
        ai_overlap, 
        left_on='filename', 
        right_on='file_name',
        how='inner'
    )
    
    # Convert human decision to binary
    merged['human_false_positive'] = merged['decision'] == 'false_positive'
    
    # Define all issue types
    issue_types = [
        'capability_issues',
        'multi_step_issues', 
        'rephrasing_issues',
        'attacker_failure_issues',
        'soft_refusal',
        'benign_elaboration'
    ]
    
    print("\n" + "="*80)
    print("DISAGREEMENT SOURCE ANALYSIS")
    print("="*80)
    
    # Calculate baseline agreement (AI considers ALL issues)
    def ai_found_any_issues(row):
        return any(row[issue] > 0.5 for issue in issue_types)
    
    merged['ai_found_any_issues'] = merged.apply(ai_found_any_issues, axis=1)
    merged['baseline_agreement'] = (merged['human_false_positive'] == ~merged['ai_found_any_issues'])
    baseline_agreement_rate = merged['baseline_agreement'].mean()
    
    print(f"Baseline agreement rate (all issues): {baseline_agreement_rate:.1%} ({merged['baseline_agreement'].sum()}/{len(merged)})")
    
    # Test excluding each issue type individually
    results = []
    
    for exclude_issue in issue_types:
        remaining_issues = [issue for issue in issue_types if issue != exclude_issue]
        
        def ai_found_remaining_issues(row):
            return any(row[issue] > 0.5 for issue in remaining_issues)
        
        merged[f'ai_found_issues_no_{exclude_issue}'] = merged.apply(ai_found_remaining_issues, axis=1)
        merged[f'agreement_no_{exclude_issue}'] = (
            merged['human_false_positive'] == ~merged[f'ai_found_issues_no_{exclude_issue}']
        )
        
        agreement_rate = merged[f'agreement_no_{exclude_issue}'].mean()
        improvement = agreement_rate - baseline_agreement_rate
        agreement_count = merged[f'agreement_no_{exclude_issue}'].sum()
        
        results.append({
            'excluded_issue': exclude_issue,
            'agreement_rate': agreement_rate,
            'agreement_count': agreement_count,
            'improvement': improvement,
            'improvement_points': improvement * 100
        })
        
        print(f"Excluding {exclude_issue:20}: {agreement_rate:.1%} ({agreement_count:2}/{len(merged)}) | Improvement: {improvement:+.1%} ({improvement*100:+.1f} points)")
    
    # Sort by improvement
    results_df = pd.DataFrame(results).sort_values('improvement', ascending=False)
    
    print("\n" + "="*80)
    print("RANKING BY IMPROVEMENT IN AGREEMENT")
    print("="*80)
    
    for i, row in results_df.iterrows():
        print(f"{row['excluded_issue']:25} | {row['agreement_rate']:.1%} | {row['improvement']:+.1%} ({row['improvement_points']:+.1f} points)")
    
    # Analyze the top disagreement source in detail
    top_issue = results_df.iloc[0]['excluded_issue']
    print(f"\n" + "="*80)
    print(f"DETAILED ANALYSIS: {top_issue.upper()}")
    print("="*80)
    
    # Cases where this issue type caused disagreement
    has_top_issue = merged[top_issue] > 0.5
    disagreement_cases = merged[~merged['baseline_agreement']]
    
    # Cases that would become agreements if we excluded this issue
    would_become_agreement = merged[merged[f'agreement_no_{top_issue}'] & ~merged['baseline_agreement']]
    
    print(f"Total files with {top_issue}: {has_top_issue.sum()}")
    print(f"Files with {top_issue} causing disagreement: {len(would_become_agreement)}")
    
    if len(would_become_agreement) > 0:
        print(f"\nBreakdown of cases that would become agreements:")
        print(f"By tactic:")
        tactic_breakdown = would_become_agreement.groupby('tactic').size().sort_values(ascending=False)
        for tactic, count in tactic_breakdown.items():
            print(f"  {tactic}: {count}")
        
        print(f"\nBy test case:")
        test_case_breakdown = would_become_agreement.groupby('test_case').size().sort_values(ascending=False)
        for test_case, count in test_case_breakdown.head(10).items():
            print(f"  {test_case}: {count}")
    
    # Test combinations of top issues
    print(f"\n" + "="*80)
    print("COMBINATION ANALYSIS (Top 3 Issues)")
    print("="*80)
    
    top_3_issues = results_df.head(3)['excluded_issue'].tolist()
    
    # Test excluding combinations
    from itertools import combinations
    
    combination_results = []
    
    for r in range(1, len(top_3_issues) + 1):
        for combo in combinations(top_3_issues, r):
            remaining_issues = [issue for issue in issue_types if issue not in combo]
            
            def ai_found_remaining_combo_issues(row):
                return any(row[issue] > 0.5 for issue in remaining_issues)
            
            combo_name = " + ".join(combo)
            merged[f'ai_found_issues_no_combo'] = merged.apply(ai_found_remaining_combo_issues, axis=1)
            merged[f'agreement_no_combo'] = (
                merged['human_false_positive'] == ~merged[f'ai_found_issues_no_combo']
            )
            
            agreement_rate = merged[f'agreement_no_combo'].mean()
            improvement = agreement_rate - baseline_agreement_rate
            agreement_count = merged[f'agreement_no_combo'].sum()
            
            combination_results.append({
                'excluded_combo': combo_name,
                'agreement_rate': agreement_rate,
                'agreement_count': agreement_count,
                'improvement': improvement,
                'improvement_points': improvement * 100
            })
    
    combo_df = pd.DataFrame(combination_results).sort_values('improvement', ascending=False)
    
    print("Best combinations for improving agreement:")
    for i, row in combo_df.head(5).iterrows():
        print(f"{row['excluded_combo']:40} | {row['agreement_rate']:.1%} | {row['improvement']:+.1%} ({row['improvement_points']:+.1f} points)")
    
    return merged, results_df, combo_df

if __name__ == "__main__":
    merged, results_df, combo_df = analyze_disagreement_sources() 