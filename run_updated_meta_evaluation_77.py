#!/usr/bin/env python3
"""
Run updated AI meta-evaluation on the 77 overlapping files between human and AI evaluators.
"""

import pandas as pd
from meta_evaluation_analysis import MetaEvaluationAnalyzer
import os
import json
from datetime import datetime
import time

def main():
    # Load the 77 overlapping files from the CSV
    df = pd.read_csv('human_ai_comparison_excluding_rephrasing.csv')
    print(f'Loading {len(df)} overlapping files...')
    
    # Initialize analyzer
    analyzer = MetaEvaluationAnalyzer()
    
    # Find file paths in batch3A
    batch3a_dir = 'clean_results/final_runs/batch3A'
    file_paths = []
    
    for filename in df['filename']:
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
    
    # Run evaluation
    results = []
    failed_files = []
    
    for i, file_path in enumerate(file_paths):
        print(f'Processing {i+1}/{len(file_paths)}: {os.path.basename(file_path)}')
        
        try:
            result = analyzer.analyze_file(file_path)
            if result:
                results.append(result)
            else:
                failed_files.append(file_path)
                print(f'  ❌ Failed to analyze')
        except Exception as e:
            failed_files.append(file_path)
            print(f'  ❌ Error: {e}')
        
        # Add small delay to avoid rate limits
        time.sleep(1)
        
        # Save progress every 10 files
        if (i + 1) % 10 == 0:
            print(f'  💾 Progress: {len(results)} successful, {len(failed_files)} failed')
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = 'updated_meta_evaluation_results_77'
    os.makedirs(output_dir, exist_ok=True)
    
    if results:
        # Save detailed results
        detailed_file = os.path.join(output_dir, f'detailed_analysis_{timestamp}.json')
        with open(detailed_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate and save summary
        summary = analyzer.generate_summary_report(results)
        summary_file = os.path.join(output_dir, f'summary_report_{timestamp}.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save CSV for comparison
        csv_file = os.path.join(output_dir, f'issue_scores_{timestamp}.csv')
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
        
        print(f'\n✅ Analysis complete!')
        print(f'Successfully analyzed: {len(results)}/{len(file_paths)} files')
        print(f'Failed: {len(failed_files)} files')
        print(f'Results saved to: {output_dir}/')
        
        if failed_files:
            print(f'\nFailed files:')
            for fp in failed_files:
                print(f'  - {os.path.basename(fp)}')
    
    else:
        print('❌ No successful analyses!')
    
    return results

if __name__ == "__main__":
    main()