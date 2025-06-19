#!/usr/bin/env python3
"""
Sample Meta-Evaluation Runner

This script runs meta-evaluation on a small sample of files for testing purposes.
Use this to validate the pipeline before running the full analysis.
"""

import os
import glob
from meta_evaluation_analysis import MetaEvaluationAnalyzer

def main():
    """Run meta-evaluation on a small sample."""
    print("Sample Meta-Evaluation Analysis")
    print("=" * 40)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your_api_key_here'")
        return 1
    
    # Find sample files (limit to 5 files from command tactic)
    batch3a_path = "clean_results/final_runs/batch3A/command"
    if not os.path.exists(batch3a_path):
        print(f"Error: Sample path not found: {batch3a_path}")
        return 1
    
    pattern = os.path.join(batch3a_path, "*.jsonl")
    all_files = glob.glob(pattern)
    all_files = [f for f in all_files if "_eval_" not in f]
    
    # Take first 5 files as sample
    sample_files = all_files[:5]
    
    if not sample_files:
        print("No sample files found")
        return 1
    
    print(f"Running analysis on {len(sample_files)} sample files:")
    for i, f in enumerate(sample_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    
    print("\nStarting analysis...")
    
    try:
        # Initialize analyzer
        analyzer = MetaEvaluationAnalyzer(api_key=api_key)
        
        # Process sample files
        results = []
        for file_path in sample_files:
            result = analyzer.analyze_file(file_path)
            if result:
                results.append(result)
        
        if not results:
            print("No results generated")
            return 1
        
        # Generate summary
        summary = analyzer.generate_summary_report(results)
        
        # Save results
        output_dir = "sample_meta_evaluation_results"
        analyzer.save_results(results, summary, output_dir)
        
        # Print summary
        print(f"\nSample Analysis Complete!")
        print(f"Analyzed {len(results)} files successfully")
        
        print("\nIssue Detection Summary:")
        for issue_type, stats in summary.get('issue_statistics', {}).items():
            high_count = stats['high_confidence_count']
            mean_score = stats['mean_score']
            print(f"  {issue_type}: {high_count} high confidence, avg score: {mean_score:.2f}")
        
        high_issue_files = summary.get('high_confidence_issues', [])
        if high_issue_files:
            print(f"\nFiles with High-Confidence Issues ({len(high_issue_files)}):")
            for item in high_issue_files:
                file_name = item['file_name']
                issue_types = [issue['issue_type'] for issue in item['issues']]
                print(f"  {file_name}: {', '.join(issue_types)}")
        else:
            print("\nNo high-confidence issues detected in sample")
        
        print(f"\nResults saved to: {output_dir}/")
        print("\nIf this looks good, run the full analysis with:")
        print("  python meta_evaluation_analysis.py")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 