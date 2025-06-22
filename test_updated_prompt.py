#!/usr/bin/env python3
"""
Test the updated AI meta-evaluator prompt on sample disagreement cases.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time

def test_updated_prompt():
    """Test updated prompt on sample disagreement cases."""
    
    # Load disagreement cases
    disagreements = pd.read_csv('disagreement_cases_for_prompt_improvement.csv')
    
    # Focus on Pattern 1 cases (human=false_positive, AI=no_issues)
    pattern1 = disagreements[
        disagreements['human_false_positive'] & (~disagreements['updated_ai_found_issues'])
    ]
    
    print(f"Testing updated prompt on {len(pattern1)} Pattern 1 disagreement cases...")
    
    # Select diverse sample for testing
    sample_files = [
        'command_airbnb_voyeurism_gemini-2.5-pro-preview-03-25_single_turn_sample1_2025_05_06_13_53_25.jsonl',
        'crowding_counterfeit_money_gemini-2.5-flash-preview_multi_turn_sample1_2025_04_21_22_07_20.jsonl',
        'command_false_accusation_gemini-2.5-pro-preview-03-25_multi_turn_sample1_2025_05_06_13_54_38.jsonl',
        'crowding_date_rape_drug_gpt-4.1-mini_multi_turn_sample1_2025_05_06_00_05_00.jsonl',
        'crowding_false_accusation_claude-3.7-sonnet_single_turn_sample1_2025_04_21_22_07_09.jsonl'
    ]
    
    # Initialize analyzer with updated prompt
    analyzer = MetaEvaluationAnalyzer()
    
    print("\\n" + "="*80)
    print("TESTING UPDATED AI META-EVALUATOR PROMPT")
    print("="*80)
    
    results = []
    batch3a_dir = 'clean_results/final_runs/batch3A'
    
    for i, filename in enumerate(sample_files, 1):
        print(f"\\n{i}. Testing: {filename}")
        print("-" * 60)
        
        # Find file path
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
            print(f"❌ File not found: {filename}")
            continue
        
        # Get human evaluation
        human_row = pattern1[pattern1['filename'] == filename]
        if human_row.empty:
            print(f"❌ No human evaluation found for: {filename}")
            continue
        
        human_decision = human_row.iloc[0]['decision']
        human_note = human_row.iloc[0]['note']
        test_case = human_row.iloc[0]['test_case']
        
        print(f"Test Case: {test_case}")
        print(f"Human Decision: {human_decision}")
        print(f"Human Note: {human_note}")
        
        # Run updated AI analysis
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                # Check if this aligns with human (false_positive = found issues)
                human_false_positive = human_decision == 'false_positive'
                agreement = human_false_positive == ai_found_issues
                
                print(f"AI Goal Achieved: {ai_goal_achieved}")
                print(f"AI Found Issues: {ai_found_issues}")
                print(f"Agreement with Human: {'✅ YES' if agreement else '❌ NO'}")
                
                # Show key issue scores
                print("\\nAI Issue Analysis:")
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result:
                        score = result[issue_type]['score']
                        if score > 0.3:  # Only show significant scores
                            print(f"  {issue_type}: {score:.2f}")
                            print(f"    Reasoning: {result[issue_type]['reasoning']}")
                
                print(f"\\nOverall Assessment: {result.get('overall_assessment', 'N/A')}")
                
                results.append({
                    'filename': filename,
                    'test_case': test_case,
                    'human_decision': human_decision,
                    'human_note': human_note,
                    'ai_goal_achieved': ai_goal_achieved,
                    'ai_found_issues': ai_found_issues,
                    'agreement': agreement
                })
            else:
                print("❌ AI analysis failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Rate limiting
        time.sleep(3)
    
    # Summary
    if results:
        agreements = sum(1 for r in results if r['agreement'])
        total = len(results)
        
        print("\\n" + "="*80)
        print("UPDATED PROMPT TEST RESULTS")
        print("="*80)
        print(f"Total cases tested: {total}")
        print(f"Agreements with humans: {agreements}")
        print(f"New agreement rate: {agreements/total:.1%}")
        print(f"Previous agreement rate: 0% (all were disagreements)")
        print(f"Improvement: +{agreements/total*100:.1f} percentage points")
        
        print("\\nCase-by-case results:")
        for i, r in enumerate(results, 1):
            status = "✅ AGREE" if r['agreement'] else "❌ DISAGREE"
            print(f"{i}. {r['test_case']:20} | {status}")
    
    return results

if __name__ == "__main__":
    test_results = test_updated_prompt()