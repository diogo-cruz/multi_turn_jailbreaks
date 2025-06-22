#!/usr/bin/env python3
"""
Collect comprehensive 0-10 scores from the 20-factor meta-evaluator prompt on the full dataset.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os
import random

def collect_comprehensive_scores(process_all=True):
    """Collect comprehensive 0-10 scores from 20-factor prompt."""
    
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
    
    if process_all:
        # Process all available cases
        sample_rows = available_rows
        print(f"Processing ALL {len(sample_rows)} available cases")
        fp_count = len([row for _, row, _ in sample_rows if row['decision'] == 'false_positive'])
        tp_count = len([row for _, row, _ in sample_rows if row['decision'] == 'true_positive'])
        print(f"Not jailbroken (false_positive): {fp_count}, Jailbroken (true_positive): {tp_count}")
    else:
        # Stratified sampling (fallback)
        fp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'false_positive']
        tp_rows = [(idx, row, fp) for idx, row, fp in available_rows if row['decision'] == 'true_positive']
        
        sample_size = 50
        fp_sample_size = int(sample_size * len(fp_rows) / len(available_rows))
        tp_sample_size = sample_size - fp_sample_size
        
        random.seed(42)
        sample_fp = random.sample(fp_rows, min(fp_sample_size, len(fp_rows)))
        sample_tp = random.sample(tp_rows, min(tp_sample_size, len(tp_rows)))
        sample_rows = sample_fp + sample_tp
        print(f"Collecting comprehensive scores from {len(sample_rows)} cases")
    
    analyzer = MetaEvaluationAnalyzer()
    
    print("\\n" + "="*80)
    print("COLLECTING COMPREHENSIVE 0-10 SCORES (20 FACTORS)")
    print("="*80)
    
    results = []
    
    # All 20 factor names for the comprehensive system
    factor_names = [
        'general_information_only', 'theoretical_vs_practical', 'incomplete_information',
        'benign_elaboration', 'substitution_deflection', 'topic_drift', 'procedural_deflection',
        'legitimate_use_reframing', 'entertainment_disclaimer', 'educational_justification',
        'hypothetical_framing', 'soft_refusal_mixed_signals', 'capability_overclaim',
        'confusion_misunderstanding', 'rephrasing_issues', 'attacker_failure',
        'multi_step_issues', 'content_gap_score', 'practical_enablement_score',
        'harmful_intent_alignment'
    ]
    
    for i, (idx, row, file_path) in enumerate(sample_rows, 1):
        filename = row['filename']
        human_decision = row['decision']
        test_case = row['test_case']
        tactic = row['jailbreak_tactic']
        
        print(f"\\n{i:3d}/{len(sample_rows)}. {test_case} - {tactic}")
        print(f"    Human: {human_decision}")
        
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Extract all 20 0-10 scores
                scores = {}
                for factor_name in factor_names:
                    if factor_name in result:
                        scores[factor_name] = result[factor_name]['score']
                    else:
                        scores[factor_name] = 0
                
                # Check agreement
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                status = "✅" if agreement else "❌"
                print(f"    AI Found Issues: {ai_found_issues} {status}")
                
                # Show top scoring factors
                top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"    Top scores: {dict(top_scores)}")
                
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
                    pd.DataFrame(results).to_csv('comprehensive_scores_sample.csv', index=False)
                    print(f"    Saved {len(results)} results so far...")
                
            else:
                print(f"    ❌ AI analysis failed")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Add base delay even for successful requests to be respectful
        time.sleep(1.0)
    
    # Final save
    if results:
        results_df = pd.DataFrame(results)
        results_df.to_csv('comprehensive_scores_sample.csv', index=False)
        
        # Quick analysis
        total = len(results)
        agreements = sum(1 for r in results if r['agreement'])
        
        print(f"\\n" + "="*80)
        print("COMPREHENSIVE SCORES COLLECTION COMPLETE")
        print("="*80)
        print(f"Total cases: {total}")
        print(f"Agreements: {agreements}")
        print(f"Agreement rate: {agreements/total:.1%}")
        
        # Show score distributions
        print(f"\\nComprehensive score statistics (0-10 scale):")
        for factor_name in factor_names:
            if factor_name in results_df.columns:
                mean_score = results_df[factor_name].mean()
                std_score = results_df[factor_name].std()
                print(f"  {factor_name}: {mean_score:.1f} ± {std_score:.1f}")
        
        print(f"\\nResults saved to comprehensive_scores_sample.csv")
        print("Ready for comprehensive AUROC analysis!")
    
    return results

if __name__ == "__main__":
    collected_results = collect_comprehensive_scores(process_all=True)  # Process all available cases