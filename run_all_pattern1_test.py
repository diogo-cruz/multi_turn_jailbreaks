#!/usr/bin/env python3
"""
Run updated prompt on all Pattern 1 disagreement cases for complete validation.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os

def run_all_pattern1_test():
    """Test updated prompt on all Pattern 1 disagreement cases."""
    
    # Load disagreement cases
    disagreements = pd.read_csv('disagreement_cases_for_prompt_improvement.csv')
    
    # Get all Pattern 1 cases (human=false_positive, AI=no_issues)
    pattern1 = disagreements[
        disagreements['human_false_positive'] & (~disagreements['updated_ai_found_issues'])
    ]
    
    print(f"Testing updated prompt on all {len(pattern1)} Pattern 1 disagreement cases...")
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("FULL PATTERN 1 TEST OF UPDATED PROMPT")
    print("="*80)
    
    results = []
    batch3a_dir = 'clean_results/final_runs/batch3A'
    agreements = 0
    
    for i, (_, row) in enumerate(pattern1.iterrows(), 1):
        filename = row['filename']
        print(f"\n{i:2d}/{len(pattern1)}. {filename}")
        
        # Find file path
        file_path = None
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                potential_path = os.path.join(tactic_path, filename)
                if os.path.exists(potential_path):
                    file_path = potential_path
                    break
        
        if not file_path:
            print(f"    ❌ File not found")
            continue
        
        # Get human info
        human_decision = row['decision']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"    {test_case} - {tactic}")
        print(f"    Human: {human_decision}")
        
        # Run AI analysis
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                if agreement:
                    agreements += 1
                    status = "✅ AGREE"
                else:
                    status = "❌ DISAGREE"
                
                print(f"    AI Found Issues: {ai_found_issues}")
                print(f"    {status}")
                
                results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'tactic': tactic,
                    'human_decision': human_decision,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                })
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Rate limiting
        if i % 5 == 0:
            print(f"\n    Progress: {i}/{len(pattern1)} ({i/len(pattern1)*100:.1f}%)")
            print(f"    Current agreement rate: {agreements}/{len(results)} ({agreements/len(results)*100:.1f}%)" if results else "")
        
        time.sleep(1.5)  # Reduced rate limiting for faster processing
    
    # Final summary
    if results:
        total = len(results)
        final_agreement_rate = agreements / total
        
        print("\n" + "="*80)
        print("FULL PATTERN 1 TEST RESULTS")
        print("="*80)
        print(f"Total cases tested: {total}")
        print(f"Agreements with humans: {agreements}")
        print(f"Final agreement rate: {final_agreement_rate:.1%}")
        print(f"Previous agreement rate: 0% (all were disagreements)")
        print(f"Total improvement: +{final_agreement_rate*100:.1f} percentage points")
        
        # Break down by test case
        print(f"\nResults by test case:")
        test_case_results = {}
        for r in results:
            tc = r['test_case']
            if tc not in test_case_results:
                test_case_results[tc] = {'total': 0, 'agreements': 0}
            test_case_results[tc]['total'] += 1
            if r['agreement']:
                test_case_results[tc]['agreements'] += 1
        
        for tc, data in sorted(test_case_results.items()):
            rate = data['agreements'] / data['total']
            print(f"  {tc:25}: {data['agreements']}/{data['total']} ({rate:.1%})")
        
        # Show remaining disagreements
        disagreement_cases = [r for r in results if not r['agreement']]
        if disagreement_cases:
            print(f"\nRemaining disagreements ({len(disagreement_cases)} cases):")
            for r in disagreement_cases:
                print(f"  {r['test_case']:20} - {r['tactic']:15} - {r['filename']}")
        else:
            print("\n🎉 NO REMAINING DISAGREEMENTS!")
    
    return results

if __name__ == "__main__":
    all_results = run_all_pattern1_test()