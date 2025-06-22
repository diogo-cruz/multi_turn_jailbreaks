#!/usr/bin/env python3
"""
Analyze disagreements excluding fake_online_profile cases and identify improvement areas.
"""

import pandas as pd
import json

def analyze_disagreements_excluding_fake_profile():
    """Analyze disagreement patterns excluding fake_online_profile cases."""
    
    # Load the comprehensive analysis results
    df = pd.read_csv('final_comprehensive_human_ai_comparison.csv')
    
    print(f"Original dataset: {len(df)} cases")
    
    # Exclude fake_online_profile cases
    df_filtered = df[df['test_case'] != 'fake_online_profile'].copy()
    print(f"After excluding fake_online_profile: {len(df_filtered)} cases")
    
    # Calculate new agreement rate
    filtered_agreement = df_filtered['agreement'].mean()
    original_agreement = df['agreement'].mean()
    
    print(f"\\n" + "="*60)
    print("AGREEMENT ANALYSIS (EXCLUDING FAKE_ONLINE_PROFILE)")
    print("="*60)
    print(f"Original agreement rate: {original_agreement:.1%}")
    print(f"Filtered agreement rate: {filtered_agreement:.1%}")
    print(f"Improvement: +{(filtered_agreement - original_agreement)*100:.1f} percentage points")
    
    # Analyze disagreement patterns
    disagreements = df_filtered[~df_filtered['agreement']].copy()
    print(f"\\nTotal disagreements: {len(disagreements)}")
    
    # Pattern 1: Human says false_positive, AI says no issues (goal achieved)
    pattern1 = disagreements[
        disagreements['human_false_positive'] & (~disagreements['updated_ai_found_issues'])
    ]
    
    # Pattern 2: Human says true_positive, AI says found issues (goal not achieved)  
    pattern2 = disagreements[
        (~disagreements['human_false_positive']) & disagreements['updated_ai_found_issues']
    ]
    
    print(f"\\nDisagreement Patterns:")
    print(f"Pattern 1 - Human: False Positive, AI: No Issues Found: {len(pattern1)} cases")
    print(f"Pattern 2 - Human: True Positive, AI: Found Issues: {len(pattern2)} cases")
    
    # Analyze Pattern 1 (main concern - humans think it's false positive but AI thinks it's valid)
    if len(pattern1) > 0:
        print(f"\\n" + "="*60)
        print("PATTERN 1 ANALYSIS: Human thinks False Positive, AI thinks Valid")
        print("="*60)
        print("These are cases where humans think the jailbreak evaluation was wrong,")
        print("but the AI meta-evaluator thinks the jailbreak was actually successful.")
        print()
        
        # Top test cases in Pattern 1
        print("Top test cases in Pattern 1:")
        pattern1_cases = pattern1['test_case'].value_counts()
        for test_case, count in pattern1_cases.head(10).items():
            print(f"  {test_case}: {count} cases")
        
        # Top tactics in Pattern 1
        print("\\nTop tactics in Pattern 1:")
        pattern1_tactics = pattern1['jailbreak_tactic'].value_counts()
        for tactic, count in pattern1_tactics.items():
            print(f"  {tactic}: {count} cases")
    
    # Analyze Pattern 2 (secondary concern)
    if len(pattern2) > 0:
        print(f"\\n" + "="*60)
        print("PATTERN 2 ANALYSIS: Human thinks True Positive, AI found Issues")
        print("="*60)
        print("These are cases where humans think the jailbreak was successful,")
        print("but the AI meta-evaluator found evaluation issues.")
        print()
        
        # Top test cases in Pattern 2
        print("Top test cases in Pattern 2:")
        pattern2_cases = pattern2['test_case'].value_counts()
        for test_case, count in pattern2_cases.head(10).items():
            print(f"  {test_case}: {count} cases")
    
    # Identify specific problematic files for testing
    print(f"\\n" + "="*60)
    print("SAMPLE FILES FOR PROMPT ITERATION")
    print("="*60)
    
    # Get diverse sample of Pattern 1 disagreements (focus area)
    if len(pattern1) > 0:
        pattern1_sample = pattern1.groupby(['test_case', 'jailbreak_tactic']).head(1)
        print(f"\\nPattern 1 sample files ({len(pattern1_sample)} files):")
        for i, (_, row) in enumerate(pattern1_sample.head(10).iterrows(), 1):
            print(f"{i:2d}. {row['filename']}")
            print(f"    Test: {row['test_case']}, Tactic: {row['jailbreak_tactic']}")
            print(f"    Human: {row['decision']}, Note: {row['note'][:100]}...")
            print()
    
    # Save filtered dataset and disagreement analysis
    df_filtered.to_csv('filtered_human_ai_comparison_no_fake_profile.csv', index=False)
    disagreements.to_csv('disagreement_cases_for_prompt_improvement.csv', index=False)
    
    print(f"Filtered dataset saved to: filtered_human_ai_comparison_no_fake_profile.csv")
    print(f"Disagreement cases saved to: disagreement_cases_for_prompt_improvement.csv")
    
    return df_filtered, disagreements, pattern1_sample.head(10) if len(pattern1) > 0 else pd.DataFrame()

if __name__ == "__main__":
    filtered_df, disagreements, sample_files = analyze_disagreements_excluding_fake_profile()