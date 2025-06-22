#!/usr/bin/env python3
"""
Test the balanced 0-10 scoring prompt on a sample of cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import random

def test_balanced_prompt():
    """Test the balanced prompt with 0-10 scoring."""
    
    # Load human evaluations
    df = pd.read_csv('false_positive_annotations.csv')
    df_filtered = df[df['test_case'] != 'fake_online_profile']
    
    # Find available files
    batch3a_dir = 'clean_results/final_runs/batch3A'
    available_rows = []
    
    for idx, row in df_filtered.iterrows():
        filename = row['filename']
        file_path = None
        
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                potential_path = os.path.join(tactic_path, filename)
                if os.path.exists(potential_path):
                    available_rows.append((idx, row, potential_path))
                    break
    
    # Sample 20 cases: 10 false_positive, 10 true_positive
    fp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'false_positive']
    tp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'true_positive']
    
    random.seed(42)
    sample_fp = random.sample(fp_rows, min(10, len(fp_rows)))
    sample_tp = random.sample(tp_rows, min(10, len(tp_rows)))
    sample_rows = sample_fp + sample_tp
    
    print(f"Testing balanced prompt on {len(sample_rows)} cases")
    print(f"False positives: {len(sample_fp)}, True positives: {len(sample_tp)}")
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("TESTING BALANCED 0-10 SCORING PROMPT")
    print("="*80)
    
    results = []
    
    for i, (idx, row, file_path) in enumerate(sample_rows, 1):
        filename = row['filename']
        human_decision = row['decision']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"\n{i:2d}/{len(sample_rows)}. {test_case} - {tactic}")
        print(f"    Human: {human_decision}")
        
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                status = "✅" if agreement else "❌"
                print(f"    AI Found Issues: {ai_found_issues} {status}")
                
                # Show issue scores
                print(f"    Issue Scores:")
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result:
                        score = result[issue_type]['score']
                        print(f"      {issue_type}: {score}")
                
                results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'tactic': tactic,
                    'human_decision': human_decision,
                    'ai_goal_achieved': ai_goal_achieved,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement,
                    'capability_issues': result.get('capability_issues', {}).get('score', 0),
                    'multi_step_issues': result.get('multi_step_issues', {}).get('score', 0),
                    'general_information_only': result.get('general_information_only', {}).get('score', 0),
                    'no_harmful_intent': result.get('no_harmful_intent', {}).get('score', 0),
                    'soft_refusal': result.get('soft_refusal', {}).get('score', 0),
                    'legitimate_use_framing': result.get('legitimate_use_framing', {}).get('score', 0)
                })
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(2)  # Rate limiting
    
    # Analysis
    if results:
        total = len(results)
        agreements = sum(1 for r in results if r['agreement'])
        
        print("\n" + "="*80)
        print("BALANCED PROMPT TEST RESULTS")
        print("="*80)
        print(f"Total cases: {total}")
        print(f"Agreements: {agreements}")
        print(f"Agreement rate: {agreements/total:.1%}")
        
        # Break down by decision type
        fp_results = [r for r in results if r['human_decision'] == 'false_positive']
        tp_results = [r for r in results if r['human_decision'] == 'true_positive']
        
        if fp_results:
            fp_agreements = sum(1 for r in fp_results if r['agreement'])
            print(f"False positive agreement: {fp_agreements}/{len(fp_results)} ({fp_agreements/len(fp_results):.1%})")
        
        if tp_results:
            tp_agreements = sum(1 for r in tp_results if r['agreement'])
            print(f"True positive agreement: {tp_agreements}/{len(tp_results)} ({tp_agreements/len(tp_results):.1%})")
        
        # Save results
        results_df = pd.DataFrame(results)
        results_df.to_csv('balanced_prompt_test_results.csv', index=False)
        print(f"\nResults saved to balanced_prompt_test_results.csv")
    
    return results

if __name__ == "__main__":
    test_results = test_balanced_prompt()