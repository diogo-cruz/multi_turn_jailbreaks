#!/usr/bin/env python3
"""
Test the updated prompt on a small sample for quick validation.
"""

from meta_evaluation_analysis import MetaEvaluationAnalyzer
import pandas as pd
import time
import os

def test_small_sample():
    """Test updated prompt on a small sample of cases."""
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    # Test just 2 specific cases to validate our approach
    test_files = [
        'command_airbnb_voyeurism_gemini-2.5-pro-preview-03-25_single_turn_sample1_2025_05_06_13_53_25.jsonl',
        'crowding_counterfeit_money_gemini-2.5-flash-preview_multi_turn_sample1_2025_04_21_22_07_20.jsonl'
    ]
    
    print("="*80)
    print("SMALL SAMPLE TEST OF UPDATED PROMPT")
    print("="*80)
    
    results = []
    batch3a_dir = 'clean_results/final_runs/batch3A'
    
    for i, filename in enumerate(test_files, 1):
        print(f"\n{i}. Testing: {filename}")
        print("-" * 60)
        
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
            print(f"❌ File not found: {filename}")
            continue
        
        # Run AI analysis
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                print(f"AI Goal Achieved: {ai_goal_achieved}")
                print(f"AI Found Issues: {ai_found_issues}")
                
                # Show main issues detected
                main_issues = []
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result and result[issue_type]['score'] > 0.5:
                        main_issues.append(f"{issue_type}:{result[issue_type]['score']:.2f}")
                
                if main_issues:
                    print(f"Main Issues: {', '.join(main_issues)}")
                else:
                    print("No significant issues detected")
                
                print(f"Overall Assessment: {result.get('overall_assessment', 'N/A')}")
                
                results.append({
                    'filename': filename,
                    'ai_goal_achieved': ai_goal_achieved,
                    'ai_found_issues': ai_found_issues,
                    'main_issues': main_issues
                })
            else:
                print(f"❌ AI analysis failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Rate limiting
        time.sleep(2)
    
    print("\n" + "="*80)
    print("SMALL SAMPLE TEST RESULTS")
    print("="*80)
    print(f"Successfully analyzed {len(results)} files")
    
    return results

if __name__ == "__main__":
    test_results = test_small_sample()