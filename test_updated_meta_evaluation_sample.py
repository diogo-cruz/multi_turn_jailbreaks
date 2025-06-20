#!/usr/bin/env python3
"""
Test updated AI meta-evaluation on key disagreement examples.
"""

import pandas as pd
from meta_evaluation_analysis import MetaEvaluationAnalyzer
import os
import json
from datetime import datetime
import time

def main():
    # Key disagreement examples from the analysis
    test_files = [
        # Examples that were in the disagreement analysis
        'crowding_counterfeit_money_claude-3.7-sonnet_multi_turn_sample1_2025_04_21_22_07_23.jsonl',
        'command_date_rape_drug_gpt-4.1_multi_turn_sample1_2025_05_06_13_53_24.jsonl',
        'command_false_accusation_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_54_40.jsonl',
        'command_airbnb_voyeurism_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_53_25.jsonl',
        'command_remove_watermarks_claude-3.7-sonnet_multi_turn_sample1_2025_05_06_13_54_02.jsonl',
        'command_lgbtq_insults_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_55_25.jsonl',
        'command_fake_online_profile_claude-3.5-sonnet_multi_turn_sample1_2025_05_06_13_53_22.jsonl',
        'command_pistol_serial_numbers_gpt-4o_multi_turn_sample1_2025_05_06_13_56_59.jsonl'
    ]
    
    print(f'Testing updated meta-evaluator on {len(test_files)} key disagreement examples...')
    
    # Load human evaluations for comparison
    df = pd.read_csv('human_ai_comparison_excluding_rephrasing.csv')
    human_data = df.set_index('filename').to_dict('index')
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    # Find file paths in batch3A
    batch3a_dir = 'clean_results/final_runs/batch3A'
    file_paths = []
    
    for filename in test_files:
        found = False
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                file_path = os.path.join(tactic_path, filename)
                if os.path.exists(file_path):
                    file_paths.append(file_path)
                    found = True
                    break
        if not found:
            print(f'Warning: Could not find {filename}')
    
    print(f'Found {len(file_paths)} files to evaluate')
    
    # Run evaluation and compare
    results = []
    agreements = 0
    disagreements = 0
    
    print('\\n' + '='*80)
    print('COMPARISON: HUMAN vs UPDATED AI META-EVALUATOR')
    print('='*80)
    
    for i, file_path in enumerate(file_paths):
        filename = os.path.basename(file_path)
        print(f'\\n{i+1}. {filename}')
        print('-' * 60)
        
        try:
            # Get AI analysis
            result = analyzer.analyze_file(file_path)
            if result:
                results.append(result)
                
                # Get human evaluation
                human_info = human_data.get(filename, {})
                human_decision = human_info.get('decision', 'unknown')
                human_false_positive = human_decision == 'false_positive'
                
                # Get AI corrected evaluation
                ai_corrected = result.get('corrected_evaluation', {})
                ai_goal_achieved = ai_corrected.get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved  # If goal not achieved, AI found issues
                
                # Compare
                agreement = human_false_positive == ai_found_issues
                if agreement:
                    agreements += 1
                    status = '✅ AGREEMENT'
                else:
                    disagreements += 1
                    status = '❌ DISAGREEMENT'
                
                print(f'Human Decision: {human_decision} (false_positive: {human_false_positive})')
                print(f'AI Corrected Goal Achieved: {ai_goal_achieved} (found_issues: {ai_found_issues})')
                print(f'Status: {status}')
                
                # Show issue scores
                print('AI Issue Scores:')
                for issue_type in analyzer.issue_categories.keys():
                    if issue_type in result:
                        score = result[issue_type]['score']
                        if score > 0.3:  # Only show non-zero scores
                            print(f'  {issue_type}: {score:.2f}')
                
                print(f'AI Assessment: {result.get("overall_assessment", "N/A")}')
                
            else:
                print('❌ Failed to analyze')
                
        except Exception as e:
            print(f'❌ Error: {e}')
        
        time.sleep(2)  # Rate limiting
    
    # Summary
    total = agreements + disagreements
    if total > 0:
        agreement_rate = agreements / total * 100
        print(f'\\n' + '='*80)
        print('SUMMARY')
        print('='*80)
        print(f'Total files analyzed: {total}')
        print(f'Agreements: {agreements} ({agreement_rate:.1f}%)')
        print(f'Disagreements: {disagreements} ({100-agreement_rate:.1f}%)')
        
        if agreement_rate > 53.2:
            improvement = agreement_rate - 53.2
            print(f'Improvement over original: +{improvement:.1f} percentage points')
        else:
            decline = 53.2 - agreement_rate
            print(f'Decline from original: -{decline:.1f} percentage points')
    
    return results

if __name__ == "__main__":
    main()