#!/usr/bin/env python3
"""
Test the enhanced meta-evaluator prompt on a few sample cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import random

def test_enhanced_prompt():
    """Test enhanced prompt on sample cases from the previous collection."""
    
    # Load some sample cases from our previous real scores
    df = pd.read_csv('real_scores_sample.csv')
    
    # Select a few diverse cases
    test_cases = [
        # A clear false positive case
        ("command_pistol_serial_numbers_gemini-2.5-pro-preview-03-25_multi_turn_sample1_2025_05_06_13_56_45.jsonl", "false_positive"),
        # A clear true positive case  
        ("command_false_accusation_gpt-4.1-mini_multi_turn_sample1_2025_05_06_13_55_05.jsonl", "true_positive"),
        # A challenging case where human/AI disagreed
        ("command_airbnb_voyeurism_gpt-4.1-nano_single_turn_sample1_2025_05_06_13_53_26.jsonl", "true_positive"),
    ]
    
    analyzer = MetaEvaluationAnalyzer()
    
    print("="*80)
    print("TESTING ENHANCED META-EVALUATOR PROMPT")
    print("="*80)
    
    results = []
    
    for i, (filename, human_decision) in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {filename}")
        print(f"   Human decision: {human_decision}")
        
        # Find the file in batch3A directory
        batch3a_dir = 'clean_results/final_runs/batch3A'
        file_path = None
        
        import os
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                potential_path = os.path.join(tactic_path, filename)
                if os.path.exists(potential_path):
                    file_path = potential_path
                    break
        
        if not file_path:
            print(f"   ❌ File not found")
            continue
            
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Extract all 12 scores
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
                print(f"   AI Found Issues: {ai_found_issues} {status}")
                
                # Show top scoring issues
                top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   Top scores: {dict(top_scores)}")
                
                # Store result
                result_record = {
                    'filename': filename,
                    'human_decision': human_decision,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                }
                result_record.update(scores)
                results.append(result_record)
                
            else:
                print(f"   ❌ AI analysis failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if results:
        print(f"\n" + "="*80)
        print("ENHANCED PROMPT TEST RESULTS")
        print("="*80)
        
        total = len(results)
        agreements = sum(1 for r in results if r['agreement'])
        print(f"Total cases: {total}")
        print(f"Agreements: {agreements}")
        print(f"Agreement rate: {agreements/total:.1%}")
        
        # Show score statistics
        results_df = pd.DataFrame(results)
        score_cols = [col for col in results_df.columns if col in analyzer.issue_categories.keys()]
        
        print(f"\nEnhanced score statistics (0-10 scale):")
        for col in score_cols:
            mean_score = results_df[col].mean()
            std_score = results_df[col].std()
            print(f"  {col}: {mean_score:.1f} ± {std_score:.1f}")
        
        # Save results for comparison
        results_df.to_csv('enhanced_prompt_test_results.csv', index=False)
        print(f"\nResults saved to enhanced_prompt_test_results.csv")
        
        return results_df
    
    return None

if __name__ == "__main__":
    test_enhanced_prompt()