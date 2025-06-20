#!/usr/bin/env python3
"""
Run updated AI meta-evaluation on the remaining 69 files from the 77 overlapping cases.
"""

import pandas as pd
from meta_evaluation_analysis import MetaEvaluationAnalyzer
import os
import json
from datetime import datetime
import time

def main():
    # Load the 77 overlapping files
    df = pd.read_csv('human_ai_comparison_excluding_rephrasing.csv')
    
    # Files already tested
    tested_files = [
        'crowding_counterfeit_money_claude-3.7-sonnet_multi_turn_sample1_2025_04_21_22_07_23.jsonl',
        'command_date_rape_drug_gpt-4.1_multi_turn_sample1_2025_05_06_13_53_24.jsonl',
        'command_false_accusation_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_54_40.jsonl',
        'command_airbnb_voyeurism_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_53_25.jsonl',
        'command_remove_watermarks_claude-3.7-sonnet_multi_turn_sample1_2025_05_06_13_54_02.jsonl',
        'command_lgbtq_insults_gemini-2.5-flash-preview_multi_turn_sample1_2025_05_06_13_55_25.jsonl',
        'command_fake_online_profile_claude-3.5-sonnet_multi_turn_sample1_2025_05_06_13_53_22.jsonl',
        'command_pistol_serial_numbers_gpt-4o_multi_turn_sample1_2025_05_06_13_56_59.jsonl'
    ]
    
    # Get remaining files
    remaining_files = [f for f in df['filename'].tolist() if f not in tested_files]
    print(f'Need to evaluate {len(remaining_files)} remaining files out of {len(df)} total')
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    # Find file paths in batch3A
    batch3a_dir = 'clean_results/final_runs/batch3A'
    file_paths = []
    
    for filename in remaining_files:
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
    
    # Run evaluation in batches with progress saving
    results = []
    failed_files = []
    batch_size = 10
    
    for i in range(0, len(file_paths), batch_size):
        batch_files = file_paths[i:i+batch_size]
        print(f'\\nProcessing batch {i//batch_size + 1}/{(len(file_paths)-1)//batch_size + 1}')
        print(f'Files {i+1}-{min(i+batch_size, len(file_paths))} of {len(file_paths)}')
        
        for j, file_path in enumerate(batch_files):
            filename = os.path.basename(file_path)
            print(f'  {i+j+1}/{len(file_paths)}: {filename}')
            
            try:
                result = analyzer.analyze_file(file_path)
                if result:
                    results.append(result)
                    print(f'    ✅ Success')
                else:
                    failed_files.append(file_path)
                    print(f'    ❌ Failed')
            except Exception as e:
                failed_files.append(file_path)
                print(f'    ❌ Error: {e}')
            
            # Rate limiting
            time.sleep(2)
        
        # Save progress after each batch
        if results:
            print(f'  💾 Batch complete. Total successful: {len(results)}, failed: {len(failed_files)}')
            
            # Save intermediate results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = f'temp_results_batch_{i//batch_size + 1}_{timestamp}.json'
            with open(temp_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f'  💾 Saved progress to {temp_file}')
        
        # Longer pause between batches
        if i + batch_size < len(file_paths):
            print(f'  ⏸️  Pausing 10 seconds between batches...')
            time.sleep(10)
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = 'complete_updated_meta_evaluation_77'
    os.makedirs(output_dir, exist_ok=True)
    
    if results:
        # Save detailed results
        detailed_file = os.path.join(output_dir, f'remaining_files_analysis_{timestamp}.json')
        with open(detailed_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate and save summary
        summary = analyzer.generate_summary_report(results)
        summary_file = os.path.join(output_dir, f'remaining_files_summary_{timestamp}.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save CSV for comparison
        csv_file = os.path.join(output_dir, f'remaining_files_scores_{timestamp}.csv')
        with open(csv_file, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            headers = ['file_name', 'tactic', 'target_model', 'original_goal_achieved', 'corrected_goal_achieved'] + list(analyzer.issue_categories.keys())
            writer.writerow(headers)
            
            for result in results:
                conv_data = result.get('conversation_data', {})
                row = [
                    result['file_name'],
                    conv_data.get('jailbreak_tactic', 'unknown'),
                    conv_data.get('target_model', 'unknown'),
                    conv_data.get('goal_achieved', False),
                    result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ]
                
                # Add issue scores
                for issue_type in analyzer.issue_categories.keys():
                    score = result.get(issue_type, {}).get('score', 0.0) if issue_type in result else 0.0
                    row.append(score)
                
                writer.writerow(row)
        
        print(f'\\n✅ Remaining files analysis complete!')
        print(f'Successfully analyzed: {len(results)}/{len(file_paths)} remaining files')
        print(f'Failed: {len(failed_files)} files')
        print(f'Results saved to: {output_dir}/')
        
        # Calculate agreement with humans for remaining files
        remaining_df = df[df['filename'].isin([os.path.basename(fp) for fp in file_paths])]
        
        agreements = 0
        total_analyzed = 0
        
        for result in results:
            filename = result['file_name']
            human_row = remaining_df[remaining_df['filename'] == filename]
            if not human_row.empty:
                human_false_positive = human_row.iloc[0]['human_false_positive']
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                if human_false_positive == ai_found_issues:
                    agreements += 1
                total_analyzed += 1
        
        if total_analyzed > 0:
            agreement_rate = agreements / total_analyzed
            print(f'\\nAgreement with humans (remaining files): {agreements}/{total_analyzed} ({agreement_rate:.1%})')
        
        if failed_files:
            print(f'\\nFailed files:')
            for fp in failed_files:
                print(f'  - {os.path.basename(fp)}')
    
    else:
        print('❌ No successful analyses!')
    
    return results

if __name__ == "__main__":
    main()