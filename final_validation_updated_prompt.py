#!/usr/bin/env python3
"""
Final validation of updated AI meta-evaluator prompt on all available cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import json

def final_validation():
    """Run final validation on all available disagreement cases."""
    
    # Load human evaluations
    human_df = pd.read_csv('false_positive_annotations.csv')
    
    # Exclude fake_online_profile as instructed
    human_df = human_df[human_df['test_case'] != 'fake_online_profile']
    
    print(f"Total human evaluations (excluding fake_online_profile): {len(human_df)}")
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("FINAL VALIDATION OF UPDATED AI META-EVALUATOR")
    print("="*80)
    
    results = []
    batch3a_dir = 'clean_results/final_runs/batch3A'
    processed = 0
    agreements = 0
    
    for i, (_, row) in enumerate(human_df.iterrows(), 1):
        filename = row['filename']
        human_decision = row['decision']
        test_case = row['test_case']
        
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
            continue
        
        processed += 1
        
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
                
                results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'human_decision': human_decision,
                    'ai_goal_achieved': ai_goal_achieved,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                })
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
        
        # Progress update
        if processed % 20 == 0:
            current_rate = agreements / len(results) if results else 0
            print(f"Progress: {processed} processed, {current_rate:.1%} agreement rate")
        
        time.sleep(1)  # Rate limiting
    
    # Final analysis
    if results:
        total = len(results)
        final_agreement_rate = agreements / total
        
        print("\n" + "="*80)
        print("FINAL VALIDATION RESULTS")
        print("="*80)
        print(f"Total cases processed: {total}")
        print(f"Total agreements: {agreements}")
        print(f"Final agreement rate: {final_agreement_rate:.1%}")
        
        # Break down by decision type
        fp_results = [r for r in results if r['human_decision'] == 'false_positive']
        tp_results = [r for r in results if r['human_decision'] == 'true_positive']
        
        fp_agreements = sum(1 for r in fp_results if r['agreement'])
        tp_agreements = sum(1 for r in tp_results if r['agreement'])
        
        print(f"\nBy human decision type:")
        print(f"  False positives: {fp_agreements}/{len(fp_results)} ({fp_agreements/len(fp_results):.1%} agreement)")
        print(f"  True positives:  {tp_agreements}/{len(tp_results)} ({tp_agreements/len(tp_results):.1%} agreement)")
        
        # Break down by test case
        print(f"\nTop disagreement test cases:")
        test_case_stats = {}
        for r in results:
            tc = r['test_case']
            if tc not in test_case_stats:
                test_case_stats[tc] = {'total': 0, 'agreements': 0}
            test_case_stats[tc]['total'] += 1
            if r['agreement']:
                test_case_stats[tc]['agreements'] += 1
        
        # Sort by disagreement rate
        disagreement_rates = []
        for tc, stats in test_case_stats.items():
            if stats['total'] >= 3:  # Only include test cases with sufficient data
                rate = stats['agreements'] / stats['total']
                disagreement_rates.append((tc, rate, stats['agreements'], stats['total']))
        
        disagreement_rates.sort(key=lambda x: x[1])  # Sort by agreement rate (lowest first)
        
        for tc, rate, agreements, total in disagreement_rates[:10]:
            print(f"  {tc:25}: {agreements}/{total} ({rate:.1%})")
        
        # Save results
        results_df = pd.DataFrame(results)
        results_df.to_csv('final_validation_results.csv', index=False)
        print(f"\nResults saved to final_validation_results.csv")
    
    return results

if __name__ == "__main__":
    validation_results = final_validation()