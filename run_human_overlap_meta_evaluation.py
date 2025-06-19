#!/usr/bin/env python3
"""
Run AI meta-evaluation on files that have human evaluations but no AI evaluations yet.
This will provide much better coverage for human vs AI comparison.
"""

import os
import json
import pandas as pd
from meta_evaluation_analysis import MetaEvaluationAnalyzer
from datetime import datetime

def load_human_evaluation_files():
    """Load list of files that have human evaluations."""
    human_files = []
    with open('clean_results/false_positive_annotations.jsonl', 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            human_files.append(data['filename'])
    return set(human_files)

def load_existing_ai_evaluations():
    """Load list of files that already have AI evaluations."""
    ai_file = 'random_100_meta_evaluation_results/issue_scores_20250617_005322.csv'
    if not os.path.exists(ai_file):
        return set()
    
    df = pd.read_csv(ai_file)
    return set(df['file_name'].tolist())

def find_files_to_evaluate():
    """Find files that need AI meta-evaluation."""
    human_files = load_human_evaluation_files()
    ai_files = load_existing_ai_evaluations()
    
    missing_files = human_files - ai_files
    print(f"Human evaluations: {len(human_files)} files")
    print(f"Existing AI evaluations: {len(ai_files)} files")
    print(f"Files needing AI evaluation: {len(missing_files)} files")
    
    return missing_files

def find_file_paths(filenames):
    """Find the full paths for the given filenames in batch3A."""
    batch3a_dir = "clean_results/final_runs/batch3A"
    file_paths = []
    
    for filename in filenames:
        # Search in all subdirectories of batch3A
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
            print(f"Warning: Could not find file {filename}")
    
    print(f"Found {len(file_paths)} files out of {len(filenames)} requested")
    return file_paths

def main():
    """Run meta-evaluation on files with human evaluations but no AI evaluations."""
    print("Finding files that need AI meta-evaluation...")
    
    # Find files that need evaluation
    missing_files = find_files_to_evaluate()
    if not missing_files:
        print("All human-evaluated files already have AI evaluations!")
        return
    
    # Find the actual file paths
    file_paths = find_file_paths(list(missing_files))
    if not file_paths:
        print("No files found to evaluate!")
        return
    
    print(f"\nRunning AI meta-evaluation on {len(file_paths)} files...")
    
    # Initialize the meta-evaluator
    analyzer = MetaEvaluationAnalyzer()
    
    # Run the evaluation on each file
    results = []
    for file_path in file_paths:
        result = analyzer.analyze_file(file_path)
        if result:
            results.append(result)
    
    # Generate summary and save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"human_overlap_meta_evaluation_results"
    
    if results:
        summary = analyzer.generate_summary_report(results)
        analyzer.save_results(results, summary, output_dir)
    
    if results:
        print(f"\n✅ Analysis complete!")
        print(f"Results saved to: {output_dir}/")
        print(f"- Detailed analysis: detailed_analysis_human_overlap_{timestamp}.json")
        print(f"- Summary report: summary_report_human_overlap_{timestamp}.json") 
        print(f"- Issue scores CSV: issue_scores_human_overlap_{timestamp}.csv")
        
        # Show new overlap count
        existing_ai = load_existing_ai_evaluations()
        new_ai_files = set([os.path.basename(fp) for fp in file_paths])
        total_ai_files = existing_ai | new_ai_files
        human_files = load_human_evaluation_files()
        new_overlap = len(human_files & total_ai_files)
        
        print(f"\nNew overlap statistics:")
        print(f"- Previous overlap: 5 files")
        print(f"- New overlap: {new_overlap} files")
        print(f"- Improvement: +{new_overlap - 5} files")
    else:
        print("❌ Analysis failed!")

if __name__ == "__main__":
    main() 