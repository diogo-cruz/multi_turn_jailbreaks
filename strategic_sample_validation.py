#!/usr/bin/env python3
"""
Strategic sampling validation of updated AI meta-evaluator on the full dataset.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import random

def strategic_sample_validation():
    """Run strategic sampling to estimate agreement on full dataset."""
    
    # Load human evaluations
    df = pd.read_csv('false_positive_annotations.csv')
    df_filtered = df[df['test_case'] != 'fake_online_profile']
    
    print(f"Total human evaluations: {len(df_filtered)}")
    
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
    
    print(f"Available files: {len(available_rows)}")
    
    # Strategic sampling: 
    # 1. Take all our known disagreement cases (Pattern 1) 
    # 2. Add stratified random sample across decision types and tactics
    
    sample_rows = []
    
    # First, add Pattern 1 cases we already tested (for consistency check)
    pattern1_files = [
        'command_airbnb_voyeurism_gemini-2.5-pro-preview-03-25_single_turn_sample1_2025_05_06_13_53_25.jsonl',
        'crowding_counterfeit_money_gemini-2.5-flash-preview_multi_turn_sample1_2025_04_21_22_07_20.jsonl',
        'command_false_accusation_gemini-2.5-pro-preview-03-25_multi_turn_sample1_2025_05_06_13_54_38.jsonl'
    ]
    
    for idx, row, file_path in available_rows:
        if row['filename'] in pattern1_files:
            sample_rows.append((idx, row, file_path))
    
    # Stratified sampling by decision type and tactic
    false_positive_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'false_positive']
    true_positive_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'true_positive']
    
    # Sample 30 from each decision type
    random.seed(42)  # For reproducibility
    fp_sample = random.sample(false_positive_rows, min(30, len(false_positive_rows)))
    tp_sample = random.sample(true_positive_rows, min(30, len(true_positive_rows)))
    
    # Combine samples (remove duplicates)
    all_sample_files = {row[1]['filename'] for row in sample_rows}
    for row_data in fp_sample + tp_sample:
        if row_data[1]['filename'] not in all_sample_files:
            sample_rows.append(row_data)
            all_sample_files.add(row_data[1]['filename'])
    
    print(f"Strategic sample size: {len(sample_rows)}")
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("STRATEGIC SAMPLE VALIDATION OF UPDATED PROMPT")
    print("="*80)
    
    results = []
    agreements = 0
    processed = 0
    
    for i, (idx, row, file_path) in enumerate(sample_rows, 1):
        filename = row['filename']
        human_decision = row['decision']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"\n{i:2d}/{len(sample_rows)}. {filename}")
        print(f"    {test_case} - {tactic} - Human: {human_decision}")
        
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                processed += 1
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                if agreement:
                    agreements += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"    AI Found Issues: {ai_found_issues} {status}")
                
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
        
        # Progress update
        if processed > 0 and processed % 10 == 0:
            current_rate = agreements / processed
            print(f"\n    Progress: {processed} processed, {current_rate:.1%} agreement rate")
        
        time.sleep(1.5)  # Rate limiting
    
    # Final analysis
    if results:
        total = len(results)
        sample_agreement_rate = agreements / total
        
        print("\n" + "="*80)
        print("STRATEGIC SAMPLE RESULTS")
        print("="*80)
        print(f"Sample size: {total}")
        print(f"Agreements: {agreements}")
        print(f"Sample agreement rate: {sample_agreement_rate:.1%}")
        
        # Break down by decision type
        fp_results = [r for r in results if r['human_decision'] == 'false_positive']
        tp_results = [r for r in results if r['human_decision'] == 'true_positive']
        
        if fp_results:
            fp_agreements = sum(1 for r in fp_results if r['agreement'])
            fp_rate = fp_agreements / len(fp_results)
            print(f"\nFalse positive cases: {fp_agreements}/{len(fp_results)} ({fp_rate:.1%} agreement)")
        
        if tp_results:
            tp_agreements = sum(1 for r in tp_results if r['agreement'])
            tp_rate = tp_agreements / len(tp_results)
            print(f"True positive cases: {tp_agreements}/{len(tp_results)} ({tp_rate:.1%} agreement)")
        
        # Estimate for full dataset
        print(f"\n" + "="*80)
        print("ESTIMATED FULL DATASET PERFORMANCE")
        print("="*80)
        print(f"Available files for evaluation: {len(available_rows)}")
        print(f"Estimated agreement rate: {sample_agreement_rate:.1%}")
        print(f"Estimated agreements: {int(sample_agreement_rate * len(available_rows))}/{len(available_rows)}")
        
        # Save results
        results_df = pd.DataFrame(results)
        results_df.to_csv('strategic_sample_validation_results.csv', index=False)
        print(f"\nResults saved to strategic_sample_validation_results.csv")
    
    return results

if __name__ == "__main__":
    validation_results = strategic_sample_validation()