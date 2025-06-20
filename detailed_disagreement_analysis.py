#!/usr/bin/env python3
"""
Detailed analysis of disagreement patterns between human and AI meta-evaluators.
This script provides deeper insights into the specific cases causing disagreement.
"""

import pandas as pd
import numpy as np
import os
import json
import textwrap
from typing import Dict, List

def load_analysis_results():
    """Load the disagreement analysis results"""
    with open('human_ai_disagreement_analysis.json', 'r') as f:
        return json.load(f)

def print_case_details(case: Dict, analysis_lookup: Dict):
    """Print detailed information about a disagreement case"""
    filename = case['filename']
    
    print("=" * 100)
    print(f"CASE: {filename}")
    print("=" * 100)
    
    print(f"Test Case: {case['test_case']}")
    print(f"Jailbreak Tactic: {case['jailbreak_tactic']}")
    print(f"Target Model: {case['target_model']}")
    print(f"Original Evaluator Decision: {case['original_evaluator_decision']}")
    print(f"Human Assessment: {case['human_assessment']}")
    print(f"AI Assessment: {case['ai_assessment']}")
    print(f"AI Corrected Goal Achieved: {case.get('ai_corrected_goal_achieved', 'N/A')}")
    
    # Get conversation data
    if filename in analysis_lookup:
        conv_data = analysis_lookup[filename].get('conversation_data', {})
        
        print(f"\nOriginal Harmful Goal: {conv_data.get('task', 'N/A')}")
        
        # Print conversation rounds
        print("\n" + "-" * 50)
        print("CONVERSATION ROUNDS:")
        print("-" * 50)
        
        round_count = 0
        for key in sorted(conv_data.keys()):
            if key.startswith('round_'):
                round_count += 1
                round_data = conv_data[key]
                
                print(f"\nROUND {round_count}:")
                print(f"Attacker Prompt: {textwrap.fill(round_data.get('tactic_prompt', 'N/A'), width=80)}")
                print(f"Target Response: {textwrap.fill(round_data.get('target_response', 'N/A'), width=80)}")
                print(f"Round Score: {round_data.get('score', 'N/A')}")
                
                if 'summary' in round_data:
                    print(f"Evaluator Summary: {textwrap.fill(round_data['summary'], width=80)}")
        
        print(f"\nFinal Goal Achieved: {conv_data.get('goal_achieved', 'N/A')}")
    
    # AI's issue analysis
    print("\n" + "-" * 50)
    print("AI META-EVALUATOR ISSUE ANALYSIS:")
    print("-" * 50)
    
    high_confidence_issues = []
    for issue_type, score in case['ai_issues_found'].items():
        if score > 0.5:
            high_confidence_issues.append(issue_type)
            print(f"\n{issue_type.upper()} (Score: {score}):")
            reasoning = case['ai_reasoning'].get(issue_type, 'N/A')
            print(textwrap.fill(reasoning, width=80, initial_indent='  ', subsequent_indent='  '))
    
    if not high_confidence_issues:
        print("No high-confidence issues found by AI.")
    
    print(f"\nAI Overall Assessment:")
    print(textwrap.fill(case['ai_overall_assessment'], width=80, initial_indent='  ', subsequent_indent='  '))
    
    print("\n" + "=" * 100)

def analyze_disagreement_patterns(results: Dict):
    """Analyze patterns in the disagreements"""
    
    print("\n" + "=" * 100)
    print("DISAGREEMENT PATTERN ANALYSIS")
    print("=" * 100)
    
    # Load original data for cross-reference
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    # Analyze each disagreement type
    patterns = results['disagreement_patterns']
    
    print(f"\nTotal disagreements: {results['disagreement_analysis']['total_disagreements']}")
    
    for pattern_name, cases in patterns.items():
        print(f"\n{pattern_name.upper()}: {len(cases)} cases")
        print("-" * 50)
        
        if pattern_name == 'both_agree_issues':
            print("These are cases where humans marked as 'true positive' but AI found evaluation issues")
            print("This suggests the AI is identifying problems with the evaluation that humans missed")
        
        elif pattern_name == 'human_fp_ai_issues':
            print("These are cases where humans marked as 'false positive' but AI found issues with the evaluation")
            print("This suggests humans correctly identified evaluation problems, but AI also found additional issues")
        
        elif pattern_name == 'human_tp_ai_no_issues':
            print("These are cases where humans marked as 'true positive' but AI found no evaluation issues")
            print("This suggests AI thinks the evaluation was correct, but humans thought it was wrong")
        
        # Show a few examples
        print(f"\nExample cases (showing first 3):")
        for i, case in enumerate(cases[:3]):
            print(f"\n{i+1}. {case['filename']}")
            print(f"   Test: {case['test_case']} | Tactic: {case['jailbreak_tactic']}")
            print(f"   Primary AI issues: {case.get('primary_issues', [])}")

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
        
        # Breakdown by tactic and test case
        print(f"\nPattern 1 by tactic:")
        # Check which tactic column exists after merge
        tactic_col = 'tactic_x' if 'tactic_x' in human_fp_ai_issues.columns else 'tactic'
        if tactic_col in human_fp_ai_issues.columns:
            tactic_counts = human_fp_ai_issues.groupby(tactic_col).size().sort_values(ascending=False)
            for tactic, count in tactic_counts.items():
                print(f"  {tactic}: {count}")
        else:
            print("  Tactic column not found")
        
        print(f"\nPattern 1 by test case (top 10):")
        # Check which test_case column exists after merge
        test_case_col = 'test_case_x' if 'test_case_x' in human_fp_ai_issues.columns else 'test_case'
        if test_case_col in human_fp_ai_issues.columns:
            test_case_counts = human_fp_ai_issues.groupby(test_case_col).size().sort_values(ascending=False)
            for test_case, count in test_case_counts.head(10).items():
                print(f"  {test_case}: {count}")
        else:
            print("  Test case column not found")
    
    # Analyze Pattern 2 if it exists
    if len(human_tp_ai_no_issues) > 0:
        print(f"\n" + "="*60)
        print("PATTERN 2 ANALYSIS: Human says 'True Positive', AI found no issues")
        print("="*60)
        
        print(f"Pattern 2 by tactic:")
        tactic_col = 'tactic_x' if 'tactic_x' in human_tp_ai_no_issues.columns else 'tactic'
        if tactic_col in human_tp_ai_no_issues.columns:
            tactic_counts = human_tp_ai_no_issues.groupby(tactic_col).size().sort_values(ascending=False)
            for tactic, count in tactic_counts.items():
                print(f"  {tactic}: {count}")
        else:
            print("  Tactic column not found")
        
        print(f"\nPattern 2 by test case:")
        test_case_col = 'test_case_x' if 'test_case_x' in human_tp_ai_no_issues.columns else 'test_case'
        if test_case_col in human_tp_ai_no_issues.columns:
            test_case_counts = human_tp_ai_no_issues.groupby(test_case_col).size().sort_values(ascending=False)
            for test_case, count in test_case_counts.items():
                print(f"  {test_case}: {count}")
        else:
            print("  Test case column not found")
    
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
    
    # Show some example disagreement cases
    print(f"\n" + "="*60)
    print("EXAMPLE DISAGREEMENT CASES")
    print("="*60)
    
    if len(human_fp_ai_issues) > 0:
        print("Examples where Human='False Positive' but AI found Issues:")
        examples = human_fp_ai_issues.head(5)
        for i, (_, row) in enumerate(examples.iterrows(), 1):
            issues_found = [issue for issue in issue_types if row[issue] > 0.5]
            print(f"\n{i}. File: {row['filename']}")
            test_case_col = 'test_case_x' if 'test_case_x' in row.index else 'test_case'
            tactic_col = 'tactic_x' if 'tactic_x' in row.index else 'tactic'
            print(f"   Test case: {row.get(test_case_col, 'Unknown')}")
            print(f"   Tactic: {row.get(tactic_col, 'Unknown')}")
            print(f"   AI found: {', '.join(issues_found)}")
            print(f"   Issue scores: {', '.join([f'{issue}={row[issue]:.2f}' for issue in issues_found])}")
    
    return merged, disagreement_cases

def main():
    """Main analysis function"""
    
    # Load analysis results
    results = load_analysis_results()
    
    # Load original data for cross-reference
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    print("DETAILED HUMAN vs AI META-EVALUATOR DISAGREEMENT ANALYSIS")
    print("=" * 100)
    
    # Analyze disagreement patterns first
    analyze_disagreement_patterns(results)
    
    print(f"\n\nDetailed case analysis will show {len(results['case_summaries'])} disagreement cases...")
    print("Press Enter to continue or 'q' to quit:")
    response = input()
    
    if response.lower() == 'q':
        return
    
    # Show detailed cases
    detailed_cases = results['disagreement_analysis']['detailed_cases']
    
    # Group by pattern for better organization
    patterns = results['disagreement_patterns']
    
    for pattern_name, pattern_cases in patterns.items():
        print(f"\n\n{'='*100}")
        print(f"DETAILED ANALYSIS: {pattern_name.upper()}")
        print(f"{'='*100}")
        
        for i, case in enumerate(pattern_cases[:5]):  # Show first 5 of each type
            print_case_details(case, analysis_lookup)
            
            if i < len(pattern_cases) - 1:
                print("\nPress Enter for next case, 's' to skip to next pattern, or 'q' to quit:")
                response = input()
                if response.lower() == 'q':
                    return
                elif response.lower() == 's':
                    break

if __name__ == "__main__":
    merged, disagreement_cases = detailed_disagreement_analysis()
    main() 