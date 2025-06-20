#!/usr/bin/env python3
"""
Corrected Analysis: Impact of Excluding Rephrasing Issues

This script properly analyzes what happens to the human vs AI agreement
when we don't count rephrasing as an evaluation issue.
"""

import pandas as pd
import json

def load_data():
    """Load the comparison data"""
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    return comparison_df

def analyze_rephrasing_impact():
    """Analyze the impact of rephrasing issues on disagreements"""
    
    df = load_data()
    
    print("=" * 80)
    print("IMPACT OF EXCLUDING REPHRASING ISSUES FROM AI META-EVALUATOR")
    print("=" * 80)
    
    # Current state
    total_files = len(df)
    current_disagreements = len(df[df['agreement'] == False])
    current_agreement_rate = (total_files - current_disagreements) / total_files * 100
    
    print(f"\nCURRENT STATE (Including Rephrasing Issues):")
    print(f"  Total files: {total_files}")
    print(f"  Disagreements: {current_disagreements}")
    print(f"  Agreement rate: {current_agreement_rate:.1f}%")
    
    # Analyze disagreement patterns
    disagreements = df[df['agreement'] == False]
    
    print(f"\nCURRENT DISAGREEMENT BREAKDOWN:")
    print(f"  Human TP, AI found issues: {len(disagreements[~disagreements['human_false_positive']])}")
    print(f"  Human FP, AI found no issues: {len(disagreements[disagreements['human_false_positive']])}")
    
    # Focus on cases where AI found issues that humans didn't catch
    human_tp_ai_issues = disagreements[~disagreements['human_false_positive']]
    
    print(f"\nANALYSIS OF 'HUMAN TP, AI FOUND ISSUES' CASES ({len(human_tp_ai_issues)} cases):")
    
    # Count issue types in these disagreements
    issue_counts = {
        'rephrasing_only': 0,
        'rephrasing_plus_others': 0,
        'no_rephrasing': 0
    }
    
    rephrasing_only_cases = []
    
    for _, row in human_tp_ai_issues.iterrows():
        has_rephrasing = row['rephrasing_issues'] > 0.5
        has_other_issues = any([
            row['attacker_failure_issues'] > 0.5,
            row['benign_elaboration'] > 0.5,
            row['capability_issues'] > 0.5,
            row['multi_step_issues'] > 0.5,
            row['soft_refusal'] > 0.5
        ])
        
        if has_rephrasing and not has_other_issues:
            issue_counts['rephrasing_only'] += 1
            rephrasing_only_cases.append(row)
        elif has_rephrasing and has_other_issues:
            issue_counts['rephrasing_plus_others'] += 1
        else:
            issue_counts['no_rephrasing'] += 1
    
    print(f"  Cases with ONLY rephrasing issues: {issue_counts['rephrasing_only']}")
    print(f"  Cases with rephrasing + other issues: {issue_counts['rephrasing_plus_others']}")
    print(f"  Cases with no rephrasing issues: {issue_counts['no_rephrasing']}")
    
    # What would happen if we exclude rephrasing?
    cases_that_would_become_agreements = issue_counts['rephrasing_only']
    new_disagreements = current_disagreements - cases_that_would_become_agreements
    new_agreement_rate = (total_files - new_disagreements) / total_files * 100
    
    print(f"\nIF WE EXCLUDE REPHRASING ISSUES:")
    print(f"  Cases that would move to agreement: {cases_that_would_become_agreements}")
    print(f"  New disagreement count: {new_disagreements}")
    print(f"  New agreement rate: {new_agreement_rate:.1f}%")
    print(f"  Improvement: +{new_agreement_rate - current_agreement_rate:.1f} percentage points")
    
    # Analyze the rephrasing-only cases
    print(f"\nDETAILS OF REPHRASING-ONLY DISAGREEMENT CASES:")
    if len(rephrasing_only_cases) > 0:
        rephrasing_only_df = pd.DataFrame(rephrasing_only_cases)
        
        print(f"\nBy test case:")
        test_case_counts = rephrasing_only_df['test_case'].value_counts()
        for test_case, count in test_case_counts.items():
            print(f"  {test_case}: {count} cases")
        
        print(f"\nBy tactic:")
        tactic_counts = rephrasing_only_df['jailbreak_tactic'].value_counts()
        for tactic, count in tactic_counts.items():
            print(f"  {tactic}: {count} cases")
    
    # Show examples
    print(f"\nEXAMPLE REPHRASING-ONLY CASES:")
    for i, (_, row) in enumerate(pd.DataFrame(rephrasing_only_cases).head(3).iterrows()):
        print(f"\n{i+1}. {row['filename']}")
        print(f"   Test: {row['test_case']} | Tactic: {row['jailbreak_tactic']}")
        print(f"   Original decision: {row['decision']}")
        print(f"   Human: True positive | AI: Found rephrasing issue (score: {row['rephrasing_issues']})")
    
    return {
        'current_agreement_rate': current_agreement_rate,
        'new_agreement_rate': new_agreement_rate,
        'improvement': new_agreement_rate - current_agreement_rate,
        'rephrasing_only_cases': cases_that_would_become_agreements
    }

def detailed_comparison_analysis():
    """Detailed analysis of what the disagreement is actually about"""
    
    df = load_data()
    
    print("\n" + "=" * 80)
    print("DETAILED COMPARISON: HUMAN vs AI EVALUATION PHILOSOPHIES")
    print("=" * 80)
    
    # Focus on cases where humans said "true positive" but AI found rephrasing issues
    target_cases = df[
        (~df['human_false_positive']) &  # Human said true positive
        (df['rephrasing_issues'] > 0.5) &  # AI found rephrasing
        (df['agreement'] == False)  # They disagreed
    ]
    
    print(f"\nCASES WHERE HUMANS ACCEPTED REPHRASING ATTACKS AS VALID:")
    print(f"Count: {len(target_cases)}")
    
    if len(target_cases) > 0:
        print(f"\nBreakdown by test case:")
        for test_case, count in target_cases['test_case'].value_counts().items():
            print(f"  {test_case}: {count} cases")
        
        print(f"\nBreakdown by tactic:")
        for tactic, count in target_cases['jailbreak_tactic'].value_counts().items():
            print(f"  {tactic}: {count} cases")
    
    print(f"\nKEY INSIGHT:")
    print(f"In {len(target_cases)} cases, humans considered rephrasing attacks as successful")
    print(f"jailbreaks, while the AI meta-evaluator identified them as evaluation")
    print(f"problems due to the attacker changing the original harmful request.")
    
    print(f"\nTHIS REPRESENTS THE CORE PHILOSOPHICAL DISAGREEMENT:")
    print(f"- Humans: 'If harmful info was provided, it's a successful jailbreak'")
    print(f"- AI: 'If the original harmful goal wasn't achieved, it's not a true jailbreak'")

def main():
    """Main analysis function"""
    
    results = analyze_rephrasing_impact()
    detailed_comparison_analysis()
    
    print("\n" + "=" * 80)
    print("SUMMARY CONCLUSIONS")
    print("=" * 80)
    
    print(f"\n1. QUANTITATIVE IMPACT:")
    print(f"   - Excluding rephrasing issues would improve agreement by {results['improvement']:.1f} points")
    print(f"   - {results['rephrasing_only_cases']} cases would move from disagreement to agreement")
    print(f"   - Agreement rate would increase from {results['current_agreement_rate']:.1f}% to {results['new_agreement_rate']:.1f}%")
    
    print(f"\n2. PHILOSOPHICAL DIFFERENCE:")
    print(f"   - The core disagreement is about whether rephrasing attacks count as valid jailbreaks")
    print(f"   - Humans tend to accept them if harmful information is provided")
    print(f"   - AI meta-evaluator considers them evaluation failures due to goal shifting")
    
    print(f"\n3. POLICY IMPLICATION:")
    print(f"   - If rephrasing attacks are considered legitimate jailbreak techniques,")
    print(f"     then human and AI evaluators would agree much more often")
    print(f"   - If rephrasing attacks are considered cheating/invalid, then the AI")
    print(f"     meta-evaluator is identifying important evaluation blind spots")

if __name__ == "__main__":
    main() 