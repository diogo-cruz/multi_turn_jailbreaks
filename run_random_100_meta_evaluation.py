#!/usr/bin/env python3
"""
Random 100 Files Meta-Evaluation Runner

This script randomly selects 100 files from batch3A and runs meta-evaluation on them.
This provides a good sample size for analysis while being manageable in terms of API costs.
"""

import os
import glob
import random
from meta_evaluation_analysis import MetaEvaluationAnalyzer

def main():
    """Run meta-evaluation on 100 randomly selected files."""
    print("Random 100 Files Meta-Evaluation Analysis")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your_api_key_here'")
        return 1
    
    # Find all files in batch3A
    batch3a_path = "clean_results/final_runs/batch3A"
    if not os.path.exists(batch3a_path):
        print(f"Error: Batch3A path not found: {batch3a_path}")
        return 1
    
    pattern = os.path.join(batch3a_path, "**", "*.jsonl")
    all_files = glob.glob(pattern, recursive=True)
    all_files = [f for f in all_files if "_eval_" not in f]
    
    if len(all_files) < 100:
        print(f"Warning: Only {len(all_files)} files found, using all of them")
        selected_files = all_files
    else:
        # Randomly select 100 files
        random.seed(42)  # For reproducibility
        selected_files = random.sample(all_files, 100)
    
    print(f"Randomly selected {len(selected_files)} files from {len(all_files)} total files")
    print("Sample selection includes files from:")
    
    # Show distribution by tactic
    tactics = {}
    for file_path in selected_files:
        parts = file_path.split(os.sep)
        if len(parts) > 1:
            tactic = parts[-2]  # Directory name should be the tactic
            tactics[tactic] = tactics.get(tactic, 0) + 1
    
    for tactic, count in sorted(tactics.items()):
        print(f"  {tactic}: {count} files")
    
    print("\nStarting analysis...")
    
    try:
        # Initialize analyzer
        analyzer = MetaEvaluationAnalyzer(api_key=api_key)
        
        # Process selected files
        results = []
        for i, file_path in enumerate(selected_files, 1):
            print(f"Progress: {i}/{len(selected_files)} - {os.path.basename(file_path)}")
            result = analyzer.analyze_file(file_path)
            if result:
                results.append(result)
        
        if not results:
            print("No results generated")
            return 1
        
        # Generate summary
        summary = analyzer.generate_summary_report(results)
        
        # Save results
        output_dir = "random_100_meta_evaluation_results"
        analyzer.save_results(results, summary, output_dir)
        
        # Print summary
        print(f"\nRandom 100 Analysis Complete!")
        print(f"Successfully analyzed {len(results)} out of {len(selected_files)} files")
        
        print("\nIssue Detection Summary:")
        for issue_type, stats in summary.get('issue_statistics', {}).items():
            high_count = stats['high_confidence_count']
            medium_count = stats['medium_confidence_count']
            mean_score = stats['mean_score']
            print(f"  {issue_type}: {high_count} high confidence, {medium_count} medium confidence, avg: {mean_score:.3f}")
        
        high_issue_files = summary.get('high_confidence_issues', [])
        multiple_issue_files = summary.get('files_with_multiple_issues', [])
        
        print(f"\nSummary Statistics:")
        print(f"  Files with high-confidence issues: {len(high_issue_files)} ({len(high_issue_files)/len(results)*100:.1f}%)")
        print(f"  Files with multiple issues: {len(multiple_issue_files)} ({len(multiple_issue_files)/len(results)*100:.1f}%)")
        
        print(f"\nResults saved to: {output_dir}/")
        
        # Show top issue types
        issue_counts = {}
        for issue_type, stats in summary.get('issue_statistics', {}).items():
            issue_counts[issue_type] = stats['high_confidence_count']
        
        print("\nMost Common Issues (high confidence):")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(results) * 100
            print(f"  {issue_type}: {count} files ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 