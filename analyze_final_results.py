#!/usr/bin/env python3
"""
Analyze the final validation results on the full 300+ dataset.
"""

import pandas as pd

def analyze_final_results():
    """Analyze the final validation results."""
    
    # Load results
    df = pd.read_csv('resumable_validation_results.csv')
    
    print("="*80)
    print("FINAL VALIDATION RESULTS ANALYSIS")
    print("="*80)
    
    total = len(df)
    agreements = sum(df['agreement'])
    agreement_rate = agreements / total
    
    print(f"Total cases analyzed: {total}")
    print(f"Total agreements: {agreements}")
    print(f"Overall agreement rate: {agreement_rate:.1%}")
    
    # Break down by decision type
    print(f"\n" + "="*60)
    print("BREAKDOWN BY HUMAN DECISION TYPE")
    print("="*60)
    
    fp_results = df[df['human_decision'] == 'false_positive']
    tp_results = df[df['human_decision'] == 'true_positive']
    
    print(f"False positive cases:")
    fp_agreements = sum(fp_results['agreement'])
    fp_total = len(fp_results)
    fp_rate = fp_agreements / fp_total if fp_total > 0 else 0
    print(f"  {fp_agreements}/{fp_total} ({fp_rate:.1%} agreement)")
    
    print(f"True positive cases:")
    tp_agreements = sum(tp_results['agreement'])
    tp_total = len(tp_results)
    tp_rate = tp_agreements / tp_total if tp_total > 0 else 0
    print(f"  {tp_agreements}/{tp_total} ({tp_rate:.1%} agreement)")
    
    # Break down by tactic
    print(f"\n" + "="*60)
    print("BREAKDOWN BY JAILBREAK TACTIC")
    print("="*60)
    
    tactics = df['tactic'].unique()
    for tactic in sorted(tactics):
        tactic_results = df[df['tactic'] == tactic]
        tactic_agreements = sum(tactic_results['agreement'])
        tactic_total = len(tactic_results)
        tactic_rate = tactic_agreements / tactic_total
        print(f"  {tactic:15}: {tactic_agreements:3}/{tactic_total:3} ({tactic_rate:.1%})")
    
    # Break down by test case
    print(f"\n" + "="*60)
    print("BREAKDOWN BY TEST CASE")
    print("="*60)
    
    test_cases = df['test_case'].value_counts()
    print("Test cases ordered by frequency:")
    for tc in test_cases.index:
        tc_results = df[df['test_case'] == tc]
        tc_agreements = sum(tc_results['agreement'])
        tc_total = len(tc_results)
        tc_rate = tc_agreements / tc_total
        print(f"  {tc:20}: {tc_agreements:3}/{tc_total:3} ({tc_rate:.1%})")
    
    # Identify disagreement patterns
    print(f"\n" + "="*60)
    print("DISAGREEMENT ANALYSIS")
    print("="*60)
    
    disagreements = df[~df['agreement']]
    print(f"Total disagreements: {len(disagreements)}")
    
    if len(disagreements) > 0:
        print(f"\nDisagreement patterns:")
        
        # Pattern 1: Human says false_positive, AI says no issues
        pattern1 = disagreements[
            (disagreements['human_decision'] == 'false_positive') & 
            (~disagreements['ai_found_issues'])
        ]
        print(f"  Pattern 1 (Human: false_positive, AI: no issues): {len(pattern1)} cases")
        
        # Pattern 2: Human says true_positive, AI says issues found
        pattern2 = disagreements[
            (disagreements['human_decision'] == 'true_positive') & 
            (disagreements['ai_found_issues'])
        ]
        print(f"  Pattern 2 (Human: true_positive, AI: found issues): {len(pattern2)} cases")
        
        # Show top disagreement test cases
        if len(disagreements) > 0:
            print(f"\nTest cases with most disagreements:")
            disagreement_by_tc = disagreements['test_case'].value_counts()
            for tc, count in disagreement_by_tc.head(5).items():
                total_for_tc = len(df[df['test_case'] == tc])
                print(f"  {tc:20}: {count}/{total_for_tc} disagreements")
    
    # Show some specific disagreement examples
    if len(disagreements) > 0:
        print(f"\nSample disagreement cases:")
        for i, (_, row) in enumerate(disagreements.head(5).iterrows()):
            print(f"  {i+1}. {row['test_case']} - {row['tactic']}")
            print(f"     Human: {row['human_decision']}, AI found issues: {row['ai_found_issues']}")
    
    # Summary statistics
    print(f"\n" + "="*60)
    print("IMPROVEMENT SUMMARY")
    print("="*60)
    
    print(f"Original baseline (before prompt improvement): ~53%")
    print(f"Current agreement rate: {agreement_rate:.1%}")
    print(f"Improvement: +{agreement_rate*100-53:.1f} percentage points")
    
    print(f"\nKey achievements:")
    print(f"• Successfully identified evaluation philosophy mismatch")
    print(f"• Rewrote AI prompt to focus on harmful intent vs general information")  
    print(f"• Achieved {fp_rate:.1%} agreement on false positive cases")
    print(f"• Achieved {tp_rate:.1%} agreement on true positive cases")
    print(f"• Validated on {total} real cases across 11 test cases and 4 tactics")

if __name__ == "__main__":
    analyze_final_results()