#!/usr/bin/env python3
"""
Resumable validation of updated AI meta-evaluator on the full dataset.
Can skip already processed cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import random
import json
import argparse

def resumable_validation(skip_existing=True, sample_size=None):
    """Run validation with option to skip already processed cases."""
    
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
    
    # Check for existing results
    existing_results = []
    results_file = 'resumable_validation_results.csv'
    
    if skip_existing and os.path.exists(results_file):
        existing_df = pd.read_csv(results_file)
        existing_results = existing_df.to_dict('records')
        existing_files = set(existing_df['filename'])
        print(f"Found {len(existing_results)} existing results, will skip those files")
    else:
        existing_files = set()
        print("Starting fresh validation")
    
    # Filter out already processed files
    remaining_rows = [(idx, row, fp) for idx, row, fp in available_rows 
                     if row['filename'] not in existing_files]
    
    print(f"Remaining files to process: {len(remaining_rows)}")
    
    # If sample_size specified, randomly sample from remaining
    if sample_size and len(remaining_rows) > sample_size:
        random.seed(42)
        remaining_rows = random.sample(remaining_rows, sample_size)
        print(f"Sampling {sample_size} files for processing")
    
    if not remaining_rows:
        print("No files to process!")
        if existing_results:
            print_summary(existing_results)
        return existing_results
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("RESUMABLE VALIDATION OF UPDATED PROMPT")
    print("="*80)
    
    new_results = []
    
    for i, (idx, row, file_path) in enumerate(remaining_rows, 1):
        filename = row['filename']
        human_decision = row['decision']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"\n{i:2d}/{len(remaining_rows)}. {filename}")
        print(f"    {test_case} - {tactic} - Human: {human_decision}")
        
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
                
                new_results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'tactic': tactic,
                    'human_decision': human_decision,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                })
                
                # Save incrementally every 10 results
                if len(new_results) % 10 == 0:
                    save_results(existing_results + new_results, results_file)
                    agreements = sum(1 for r in existing_results + new_results if r['agreement'])
                    total = len(existing_results + new_results)
                    print(f"    Progress: {total} total, {agreements/total:.1%} agreement rate")
                    
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(1.5)  # Rate limiting
    
    # Combine all results
    all_results = existing_results + new_results
    
    # Save final results
    if new_results:
        save_results(all_results, results_file)
    
    print_summary(all_results)
    return all_results

def save_results(results, filename):
    """Save results to CSV."""
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)

def print_summary(results):
    """Print summary statistics."""
    if not results:
        return
        
    total = len(results)
    agreements = sum(1 for r in results if r['agreement'])
    agreement_rate = agreements / total
    
    print("\n" + "="*80)
    print("VALIDATION RESULTS SUMMARY")
    print("="*80)
    print(f"Total cases: {total}")
    print(f"Agreements: {agreements}")
    print(f"Overall agreement rate: {agreement_rate:.1%}")
    
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
    
    # Break down by tactic
    print(f"\nBy tactic:")
    tactics = set(r['tactic'] for r in results)
    for tactic in sorted(tactics):
        tactic_results = [r for r in results if r['tactic'] == tactic]
        tactic_agreements = sum(1 for r in tactic_results if r['agreement'])
        tactic_rate = tactic_agreements / len(tactic_results)
        print(f"  {tactic:15}: {tactic_agreements}/{len(tactic_results)} ({tactic_rate:.1%})")

def main():
    parser = argparse.ArgumentParser(description='Resumable validation of AI meta-evaluator')
    parser.add_argument('--no-skip', action='store_true', 
                       help='Start fresh, do not skip existing results')
    parser.add_argument('--sample-size', type=int, 
                       help='Only process this many files (for testing)')
    
    args = parser.parse_args()
    
    skip_existing = not args.no_skip
    resumable_validation(skip_existing=skip_existing, sample_size=args.sample_size)

if __name__ == "__main__":
    main()