#!/usr/bin/env python3
"""
Run updated AI meta-evaluation on the 197 new human evaluation cases.
"""

import pandas as pd
from meta_evaluation_analysis import MetaEvaluationAnalyzer
import os
import json
from datetime import datetime
import time

def main():
    # Load the new cases to process
    new_cases_df = pd.read_csv('new_human_evaluations_to_process.csv')
    print(f'Processing {len(new_cases_df)} new human evaluation cases...')
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    # Find file paths in batch3A for available files
    batch3a_dir = 'clean_results/final_runs/batch3A'
    file_paths = []
    missing_files = []
    
    for _, row in new_cases_df.iterrows():
        filename = row['filename']
        found = False
        
        # Search in all subdirectories of batch3A
        for tactic_dir in os.listdir(batch3a_dir):
            tactic_path = os.path.join(batch3a_dir, tactic_dir)
            if os.path.isdir(tactic_path):
                file_path = os.path.join(tactic_path, filename)
                if os.path.exists(file_path):
                    file_paths.append(file_path)
                    found = True
                    break
        
        if not found:
            missing_files.append(filename)
    
    print(f'Found {len(file_paths)} files to evaluate')
    print(f'Missing {len(missing_files)} files')
    
    # Run evaluation in manageable batches
    results = []
    failed_files = []
    batch_size = 20  # Larger batches since API is working well
    
    total_batches = (len(file_paths) - 1) // batch_size + 1
    
    for i in range(0, len(file_paths), batch_size):
        batch_files = file_paths[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        print(f'\\nProcessing batch {batch_num}/{total_batches}')
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
            time.sleep(1.5)
        
        # Save progress after each batch
        if results:
            print(f'  💾 Batch {batch_num} complete. Total successful: {len(results)}, failed: {len(failed_files)}')
            
            # Save intermediate results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = f'temp_new_results_batch_{batch_num}_{timestamp}.json'
            with open(temp_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f'  💾 Saved progress to {temp_file}')
        
        # Pause between batches
        if i + batch_size < len(file_paths):
            print(f'  ⏸️  Pausing 15 seconds between batches...')
            time.sleep(15)
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = 'new_cases_meta_evaluation_results'
    os.makedirs(output_dir, exist_ok=True)
    
    if results:
        # Save detailed results
        detailed_file = os.path.join(output_dir, f'new_cases_analysis_{timestamp}.json')
        with open(detailed_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate and save summary
        summary = analyzer.generate_summary_report(results)
        summary_file = os.path.join(output_dir, f'new_cases_summary_{timestamp}.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save CSV for comparison
        csv_file = os.path.join(output_dir, f'new_cases_scores_{timestamp}.csv')
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
        
        print(f'\\n✅ New cases analysis complete!')
        print(f'Successfully analyzed: {len(results)}/{len(file_paths)} new files')
        print(f'Failed: {len(failed_files)} files')
        print(f'Results saved to: {output_dir}/')
        
        # Calculate agreement with humans for new cases
        agreements = 0
        total_analyzed = 0
        
        for result in results:
            filename = result['file_name']
            human_row = new_cases_df[new_cases_df['filename'] == filename]
            if not human_row.empty:
                human_decision = human_row.iloc[0]['decision']
                human_false_positive = human_decision == 'false_positive'
                ai_goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                ai_found_issues = not ai_goal_achieved
                
                if human_false_positive == ai_found_issues:
                    agreements += 1
                total_analyzed += 1
        
        if total_analyzed > 0:
            agreement_rate = agreements / total_analyzed
            print(f'\\nAgreement with humans (new cases): {agreements}/{total_analyzed} ({agreement_rate:.1%})')
        
        if failed_files:
            print(f'\\nFailed files (first 10):')
            for i, fp in enumerate(failed_files[:10]):
                print(f'  {i+1}. {os.path.basename(fp)}')
            if len(failed_files) > 10:
                print(f'  ... and {len(failed_files) - 10} more')
    
    else:
        print('❌ No successful analyses!')
    
    return results

if __name__ == "__main__":
    main()