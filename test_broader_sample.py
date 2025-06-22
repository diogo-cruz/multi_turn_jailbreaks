#!/usr/bin/env python3
"""
Test the updated prompt on a broader sample of disagreement cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os

def test_broader_sample():
    """Test updated prompt on broader sample of disagreement cases."""
    
    # Load disagreement cases
    disagreements = pd.read_csv('disagreement_cases_for_prompt_improvement.csv')
    
    # Take a diverse sample of Pattern 1 cases (human=false_positive, AI=no_issues)
    pattern1 = disagreements[
        disagreements['human_false_positive'] & (~disagreements['updated_ai_found_issues'])
    ]
    
    print(f"Total Pattern 1 disagreements: {len(pattern1)}")
    
    # Select diverse sample by test case and tactic (reduce to 10 for faster testing)
    sample_cases = pattern1.groupby(['test_case', 'jailbreak_tactic']).head(1).head(10)
    
    print(f"Testing broader sample: {len(sample_cases)} cases")
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    results = []
    batch3a_dir = 'clean_results/final_runs/batch3A'
    
    print("\\n" + "="*80)
    print("BROADER SAMPLE TEST OF UPDATED PROMPT")
    print("="*80)
    
    for i, (_, row) in enumerate(sample_cases.iterrows(), 1):
        filename = row['filename']
        print(f"\\n{i:2d}. {filename}")
        
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
        human_note = row['note']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"    Test: {test_case}, Tactic: {tactic}")
        print(f"    Human: {human_decision} - {human_note[:60]}...")
        
        # Run AI analysis
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                print(f"    AI Found Issues: {ai_found_issues}")
                print(f"    Agreement: {'✅ YES' if agreement else '❌ NO'}")
                
                # Show main issues detected
                main_issues = []
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result and result[issue_type]['score'] > 0.5:
                        main_issues.append(issue_type)
                
                if main_issues:
                    print(f"    Main Issues: {', '.join(main_issues)}")
                
                results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'tactic': tactic,
                    'human_decision': human_decision,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement,
                    'main_issues': main_issues
                })
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Rate limiting
        time.sleep(2)
    
    # Summary analysis
    if results:
        agreements = sum(1 for r in results if r['agreement'])
        total = len(results)
        
        print("\\n" + "="*80)
        print("BROADER SAMPLE TEST RESULTS")
        print("="*80)
        print(f"Total cases tested: {total}")
        print(f"Agreements with humans: {agreements}")
        print(f"New agreement rate: {agreements/total:.1%}")
        print(f"Previous agreement rate: 0% (all were disagreements)")
        print(f"Improvement: +{agreements/total*100:.1f} percentage points")
        
        # Break down by test case
        print("\\nResults by test case:")
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
            print(f"  {tc:20}: {data['agreements']}/{data['total']} ({rate:.1%})")
        
        # Show disagreements if any
        disagreement_cases = [r for r in results if not r['agreement']]
        if disagreement_cases:
            print(f"\\nRemaining disagreements ({len(disagreement_cases)} cases):")
            for r in disagreement_cases:
                print(f"  {r['test_case']} - {r['tactic']}")
        else:
            print("\\n🎉 NO REMAINING DISAGREEMENTS!")
    
    return results

if __name__ == "__main__":
    broader_results = test_broader_sample()