#!/usr/bin/env python3
"""
Collect real 0-10 scores from the balanced prompt on a strategic sample.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import random

def collect_real_scores(sample_size=50):
    """Collect real 0-10 scores from balanced prompt."""
    
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
    
    # Stratified sampling
    fp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'false_positive']
    tp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'true_positive']
    
    # Sample proportionally 
    fp_sample_size = int(sample_size * len(fp_rows) / len(available_rows))
    tp_sample_size = sample_size - fp_sample_size
    
    random.seed(42)
    sample_fp = random.sample(fp_rows, min(fp_sample_size, len(fp_rows)))
    sample_tp = random.sample(tp_rows, min(tp_sample_size, len(tp_rows)))
    sample_rows = sample_fp + sample_tp
    
    print(f"Collecting real scores from {len(sample_rows)} cases")
    print(f"False positives: {len(sample_fp)}, True positives: {len(sample_tp)}")
    
    analyzer = MetaEvaluationAnalyzer()
    
    print("\n" + "="*80)
    print("COLLECTING REAL 0-10 SCORES")
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
                
                # Extract 0-10 scores
                scores = {}
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result:
                        scores[issue_type] = result[issue_type]['score']
                    else:
                        scores[issue_type] = 0
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                status = "✅" if agreement else "❌"
                print(f"    AI Found Issues: {ai_found_issues} {status}")
                print(f"    Scores: {scores}")
                
                # Create result record
                result_record = {
                    'filename': filename,
                    'test_case': test_case,
                    'tactic': tactic,
                    'human_decision': human_decision,
                    'ai_goal_achieved': ai_goal_achieved,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                }
                result_record.update(scores)
                results.append(result_record)
                
                # Save incrementally
                if len(results) % 10 == 0:
                    pd.DataFrame(results).to_csv('real_scores_sample.csv', index=False)
                    print(f"    Saved {len(results)} results so far...")
                
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(1.5)  # Rate limiting
    
    # Final save
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv('real_scores_sample.csv', index=False)
        
        # Quick analysis
        total = len(results)
        agreements = sum(1 for r in results if r['agreement'])
        
        print(f"\n" + "="*80)
        print("REAL SCORES COLLECTION COMPLETE")
        print("="*80)
        print(f"Total cases: {total}")
        print(f"Agreements: {agreements}")
        print(f"Agreement rate: {agreements/total:.1%}")
        
        # Show score distributions
        score_cols = [col for col in results_df.columns if col in analyzer.issue_categories.keys()]
        print(f"\nScore statistics (0-10 scale):")
        for col in score_cols:
            mean_score = results_df[col].mean()
            std_score = results_df[col].std()
            print(f"  {col}: {mean_score:.1f} ± {std_score:.1f}")
        
        print(f"\nResults saved to real_scores_sample.csv")
        print("Ready for AUROC analysis!")
    
    return results

if __name__ == "__main__":
    collected_results = collect_real_scores(sample_size=30)  # Start with 30 cases