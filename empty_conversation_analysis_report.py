#!/usr/bin/env python3
"""
Final comprehensive analysis and report on empty/problematic conversation files.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import argparse

def detailed_file_analysis(file_path):
    """Detailed analysis of a single JSONL file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        analysis = {
            'path': str(file_path),
            'total_lines': len(lines),
            'file_size_bytes': os.path.getsize(file_path),
            'has_metadata': False,
            'conversation_rounds': 0,
            'complete_rounds': 0,
            'error_rounds': 0,
            'attacker_refused_rounds': 0,
            'api_error_rounds': 0,
            'has_goal_achieved': False,
            'goal_achieved_value': None,
            'errors': [],
            'status': 'unknown'
        }
        
        if len(lines) == 0:
            analysis['status'] = 'empty_file'
            return analysis
        
        goal_achieved_line = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Check for metadata (first line)
                if line_num == 1:
                    metadata_fields = ['model_base_url', 'target_model', 'test_case', 'jailbreak_tactic']
                    if any(field in data for field in metadata_fields):
                        analysis['has_metadata'] = True
                
                # Check for conversation rounds
                if 'round' in data:
                    analysis['conversation_rounds'] += 1
                    
                    if 'error' in data:
                        analysis['error_rounds'] += 1
                        error_msg = data['error']
                        if 'Attacker refused' in error_msg:
                            analysis['attacker_refused_rounds'] += 1
                        elif 'API error' in error_msg or 'Error code:' in error_msg:
                            analysis['api_error_rounds'] += 1
                    
                    elif 'user' in data and 'assistant' in data:
                        analysis['complete_rounds'] += 1
                
                # Check for goal_achieved
                if 'goal_achieved' in data:
                    analysis['has_goal_achieved'] = True
                    analysis['goal_achieved_value'] = data['goal_achieved']
                    goal_achieved_line = line_num
                    
            except json.JSONDecodeError as e:
                analysis['errors'].append(f"Line {line_num}: JSON decode error - {e}")
        
        # Determine status
        if not analysis['has_metadata']:
            analysis['status'] = 'no_metadata'
        elif analysis['conversation_rounds'] == 0:
            analysis['status'] = 'metadata_only'
        elif analysis['error_rounds'] > 0 and analysis['complete_rounds'] == 0:
            if analysis['attacker_refused_rounds'] > 0:
                analysis['status'] = 'attacker_refused'
            elif analysis['api_error_rounds'] > 0:
                analysis['status'] = 'api_errors_only'
            else:
                analysis['status'] = 'other_errors_only'
        elif analysis['complete_rounds'] > 0:
            analysis['status'] = 'has_conversation'
        else:
            analysis['status'] = 'mixed_errors_conversation'
        
        return analysis
        
    except Exception as e:
        return {
            'path': str(file_path),
            'status': 'file_read_error',
            'error': str(e),
            'total_lines': 0,
            'file_size_bytes': 0
        }

def extract_file_metadata(filename):
    """Extract metadata from filename."""
    parts = filename.split('_')
    
    # Extract directory (tactic)
    tactic = filename.split('/')[0] if '/' in filename else 'unknown'
    
    metadata = {
        'tactic': tactic,
        'test_case': 'unknown',
        'model': 'unknown',
        'turn_type': 'unknown',
        'sample': 'unknown',
        'reasoning': 'unknown'
    }
    
    # Extract test case (usually second part after tactic)
    if len(parts) > 1:
        metadata['test_case'] = parts[1]
    
    # Find turn type and extract model
    for i, part in enumerate(parts):
        if part in ['single_turn', 'multi_turn']:
            metadata['turn_type'] = part
            # Model parts are between test_case and turn_type
            if i > 2:
                model_parts = parts[2:i]
                metadata['model'] = '_'.join(model_parts)
            break
    
    # Extract sample number
    for part in parts:
        if part.startswith('sample'):
            metadata['sample'] = part
            break
    
    # Extract reasoning level (for batch6C)
    if 'reasoning_high' in filename:
        metadata['reasoning'] = 'high'
    elif 'reasoning_low' in filename:
        metadata['reasoning'] = 'low'
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description='Comprehensive analysis of conversation data quality')
    parser.add_argument('--detailed-report', action='store_true',
                       help='Generate detailed report with examples')
    args = parser.parse_args()
    
    base_dir = Path("/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs")
    batches = ['batch6A', 'batch6B', 'batch6C']
    
    print("COMPREHENSIVE CONVERSATION DATA QUALITY ANALYSIS")
    print("=" * 80)
    print()
    
    all_analyses = {}
    batch_summaries = {}
    
    for batch in batches:
        batch_dir = base_dir / batch
        print(f"Analyzing {batch}...")
        
        batch_analyses = {}
        status_counts = Counter()
        
        # Analyze all JSONL files
        for jsonl_file in batch_dir.rglob("*.jsonl"):
            relative_path = str(jsonl_file.relative_to(batch_dir))
            analysis = detailed_file_analysis(jsonl_file)
            batch_analyses[relative_path] = analysis
            status_counts[analysis['status']] += 1
        
        all_analyses[batch] = batch_analyses
        batch_summaries[batch] = {
            'total_files': len(batch_analyses),
            'status_counts': status_counts
        }
        
        print(f"  Files analyzed: {len(batch_analyses)}")
        for status, count in status_counts.most_common():
            print(f"    {status}: {count}")
        print()
    
    # Overall summary
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    total_files = sum(batch_summaries[batch]['total_files'] for batch in batches)
    overall_status_counts = Counter()
    
    for batch in batches:
        for status, count in batch_summaries[batch]['status_counts'].items():
            overall_status_counts[status] += count
    
    print(f"Total files analyzed: {total_files}")
    print()
    print("Status distribution:")
    for status, count in overall_status_counts.most_common():
        percentage = (count / total_files) * 100
        print(f"  {status:25} {count:4d} files ({percentage:5.1f}%)")
    
    # Problem analysis
    print("\n" + "PROBLEM ANALYSIS")
    print("=" * 80)
    
    problem_categories = {
        'metadata_only': 'Files with only metadata, no conversation attempts',
        'attacker_refused': 'Files where the attacker model refused to generate prompts',
        'api_errors_only': 'Files with only API errors',
        'other_errors_only': 'Files with other types of errors',
        'file_read_error': 'Files that could not be read',
        'no_metadata': 'Files without proper metadata'
    }
    
    total_problems = 0
    for problem_type in problem_categories.keys():
        count = overall_status_counts[problem_type]
        total_problems += count
        if count > 0:
            print(f"  {problem_categories[problem_type]}: {count} files")
    
    print(f"\nTotal problematic files: {total_problems} ({total_problems/total_files*100:.1f}%)")
    print(f"Files with successful conversations: {overall_status_counts['has_conversation']} ({overall_status_counts['has_conversation']/total_files*100:.1f}%)")
    
    # Pattern analysis for problematic files
    print("\n" + "PATTERN ANALYSIS FOR PROBLEMATIC FILES")
    print("=" * 80)
    
    problem_files = []
    for batch, batch_analyses in all_analyses.items():
        for filename, analysis in batch_analyses.items():
            if analysis['status'] in problem_categories.keys():
                file_metadata = extract_file_metadata(filename)
                file_metadata['batch'] = batch
                file_metadata['status'] = analysis['status']
                file_metadata['filename'] = filename
                problem_files.append(file_metadata)
    
    if problem_files:
        print(f"Analyzing {len(problem_files)} problematic files:")
        print()
        
        # By batch
        batch_problem_counts = Counter(f['batch'] for f in problem_files)
        print("Problems by batch:")
        for batch, count in batch_problem_counts.most_common():
            print(f"  {batch}: {count}")
        print()
        
        # By model
        model_problem_counts = Counter(f['model'] for f in problem_files)
        print("Problems by model:")
        for model, count in model_problem_counts.most_common()[:10]:
            print(f"  {model}: {count}")
        print()
        
        # By tactic
        tactic_problem_counts = Counter(f['tactic'] for f in problem_files)
        print("Problems by tactic:")
        for tactic, count in tactic_problem_counts.most_common():
            print(f"  {tactic}: {count}")
        print()
        
        # By test case
        test_case_problem_counts = Counter(f['test_case'] for f in problem_files)
        print("Problems by test case:")
        for test_case, count in test_case_problem_counts.most_common():
            print(f"  {test_case}: {count}")
        print()
        
        # By problem type
        status_problem_counts = Counter(f['status'] for f in problem_files)
        print("Problems by type:")
        for status, count in status_problem_counts.most_common():
            print(f"  {status}: {count}")
    
    # Detailed examples if requested
    if args.detailed_report:
        print("\n" + "DETAILED EXAMPLES")
        print("=" * 80)
        
        for problem_type in problem_categories.keys():
            examples = [f for f in problem_files if f['status'] == problem_type]
            if examples:
                print(f"\n{problem_type.upper()} Examples:")
                for example in examples[:3]:  # Show first 3 examples
                    print(f"  {example['batch']}/{example['filename']}")
                if len(examples) > 3:
                    print(f"  ... and {len(examples) - 3} more")
    
    print(f"\nAnalysis complete. Report covers {total_files} files across {len(batches)} batches.")

if __name__ == "__main__":
    main()