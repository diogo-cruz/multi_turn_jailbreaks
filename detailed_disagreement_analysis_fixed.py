#!/usr/bin/env python3
"""
Detailed analysis of disagreement patterns between human and AI meta-evaluators.
This script provides deeper insights into the specific cases causing disagreement.
"""

import pandas as pd
import numpy as np
import os
import json

def load_human_evaluations(filepath):
    """Load human evaluation data from JSONL file."""
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

def detailed_disagreement_analysis():
    """Provide detailed analysis of disagreement patterns."""
    
    # Load data
    ai_df = pd.read_csv('combined_meta_evaluation_results/issue_scores_combined_20250617_064347.csv')
    human_df = load_human_evaluations('clean_results/false_positive_annotations.jsonl')
    
    # Find overlapping files and merge
    overlap_files = set(human_df['filename']) & set(ai_df['file_name'])
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
    
    # Define issue types
    issue_types = [
        'capability_issues',
        'multi_step_issues', 
        'rephrasing_issues',
        'attacker_failure_issues',
        'soft_refusal',
        'benign_elaboration'
    ]
    
    # Calculate AI found issues
    def ai_found_any_issues(row):
        return any(row[issue] > 0.5 for issue in issue_types)
    
    merged['ai_found_any_issues'] = merged.apply(ai_found_any_issues, axis=1)
    merged['agreement'] = (merged['human_false_positive'] == ~merged['ai_found_any_issues'])
    
    print("="*80)
    print("DETAILED DISAGREEMENT ANALYSIS")
    print("="*80)
    
    # Overall breakdown
    total_files = len(merged)
    agreements = merged['agreement'].sum()
    disagreements = total_files - agreements
    
    print(f"Total files: {total_files}")
    print(f"Agreements: {agreements} ({agreements/total_files:.1%})")
    print(f"Disagreements: {disagreements} ({disagreements/total_files:.1%})")
    
    # Disagreement patterns
    disagreement_cases = merged[~merged['agreement']].copy()
    
    print(f"\n" + "="*60)
    print("DISAGREEMENT PATTERNS")
    print("="*60)
    
    # Pattern 1: Human says "false positive" but AI found issues
    human_fp_ai_issues = disagreement_cases[
        disagreement_cases['human_false_positive'] & disagreement_cases['ai_found_any_issues']
    ]
    
    # Pattern 2: Human says "true positive" but AI found no issues  
    human_tp_ai_no_issues = disagreement_cases[
        ~disagreement_cases['human_false_positive'] & ~disagreement_cases['ai_found_any_issues']
    ]
    
    print(f"Pattern 1 - Human: 'False Positive', AI: 'Found Issues': {len(human_fp_ai_issues)} cases")
    print(f"Pattern 2 - Human: 'True Positive', AI: 'No Issues': {len(human_tp_ai_no_issues)} cases")
    
    # Analyze Pattern 1 in detail (most common)
    if len(human_fp_ai_issues) > 0:
        print(f"\n" + "="*60)
        print("PATTERN 1 ANALYSIS: Human says 'False Positive', AI found issues")
        print("="*60)
        
        # Which issues does AI find in these cases?
        print("AI issue detection in Pattern 1 cases:")
        for issue in issue_types:
            count = (human_fp_ai_issues[issue] > 0.5).sum()
            percentage = count / len(human_fp_ai_issues) * 100
            print(f"  {issue:25}: {count:2}/{len(human_fp_ai_issues)} ({percentage:5.1f}%)")
        
        # Issue combinations in Pattern 1
        print(f"\nIssue combinations in Pattern 1:")
        pattern1_issues = []
        for _, row in human_fp_ai_issues.iterrows():
            issues_found = [issue for issue in issue_types if row[issue] > 0.5]
            pattern1_issues.append(tuple(sorted(issues_found)))
        
        from collections import Counter
        issue_combos = Counter(pattern1_issues)
        
        print("Most common issue combinations:")
        for combo, count in issue_combos.most_common(10):
            print(f"  {' + '.join(combo) if combo else 'No issues'}: {count}")
    
    # Analyze rephrasing impact specifically
    print(f"\n" + "="*60)
    print("REPHRASING ISSUE ANALYSIS")
    print("="*60)
    
    # Cases with high rephrasing scores
    high_rephrasing = merged[merged['rephrasing_issues'] > 0.5]
    print(f"Files with high rephrasing scores (>0.5): {len(high_rephrasing)}")
    
    # Rephrasing in disagreement cases
    disagreement_rephrasing = disagreement_cases[disagreement_cases['rephrasing_issues'] > 0.5]
    print(f"Disagreement cases with rephrasing: {len(disagreement_rephrasing)}")
    
    # Cases where ONLY rephrasing causes the disagreement
    def has_only_rephrasing(row):
        other_issues = [issue for issue in issue_types if issue != 'rephrasing_issues']
        return (row['rephrasing_issues'] > 0.5) and not any(row[issue] > 0.5 for issue in other_issues)
    
    only_rephrasing_disagreements = disagreement_cases[disagreement_cases.apply(has_only_rephrasing, axis=1)]
    print(f"Disagreements caused ONLY by rephrasing: {len(only_rephrasing_disagreements)}")
    
    # What would happen if we excluded rephrasing?
    def ai_found_non_rephrasing_issues(row):
        non_rephrasing_issues = [issue for issue in issue_types if issue != 'rephrasing_issues']
        return any(row[issue] > 0.5 for issue in non_rephrasing_issues)
    
    merged['ai_found_non_rephrasing'] = merged.apply(ai_found_non_rephrasing_issues, axis=1)
    merged['agreement_no_rephrasing'] = (merged['human_false_positive'] == ~merged['ai_found_non_rephrasing'])
    
    new_agreements = merged['agreement_no_rephrasing'].sum()
    improvement = new_agreements - agreements
    
    print(f"\nIf we excluded rephrasing issues:")
    print(f"  New agreement rate: {new_agreements}/{total_files} ({new_agreements/total_files:.1%})")
    print(f"  Change in agreements: {improvement:+d} ({improvement/total_files:+.1%})")
    
    # Which specific cases would change?
    would_become_agreements = merged[merged['agreement_no_rephrasing'] & ~merged['agreement']]
    would_become_disagreements = merged[~merged['agreement_no_rephrasing'] & merged['agreement']]
    
    print(f"  Cases that would become agreements: {len(would_become_agreements)}")
    print(f"  Cases that would become disagreements: {len(would_become_disagreements)}")
    
    return merged, disagreement_cases

if __name__ == "__main__":
    merged, disagreement_cases = detailed_disagreement_analysis() 