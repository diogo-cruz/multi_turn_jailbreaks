#!/usr/bin/env python3
"""
Corrected analysis of JSONL files to properly identify files with conversation rounds.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import argparse

def analyze_jsonl_file_corrected(file_path):
    """
    Corrected analysis that looks for actual conversation data in the JSONL structure.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        if total_lines == 0:
            return {
                'status': 'empty',
                'total_lines': 0,
                'conversation_rounds': 0,
                'has_metadata': False,
                'has_actual_conversation': False,
                'error': None,
                'file_size': os.path.getsize(file_path)
            }
        
        conversation_rounds = 0
        has_metadata = False
        has_actual_conversation = False
        parsed_lines = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                parsed_lines += 1
                
                # Check for metadata in first line
                if line_num == 1:
                    metadata_fields = ['model_base_url', 'target_model', 'test_case', 'jailbreak_tactic', 'timestamp']
                    if any(field in data for field in metadata_fields):
                        has_metadata = True
                
                # Check for conversation rounds (lines with "round" field)
                if 'round' in data:
                    conversation_rounds += 1
                    if 'user' in data and 'assistant' in data:
                        has_actual_conversation = True
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error in {file_path} line {line_num}: {e}")
                continue
        
        # Determine status based on corrected logic
        if has_metadata and conversation_rounds == 0:
            status = 'metadata_only'
        elif has_metadata and conversation_rounds > 0 and not has_actual_conversation:
            status = 'incomplete_conversation'
        elif has_metadata and has_actual_conversation:
            status = 'complete_conversation'
        elif conversation_rounds == 0 and not has_metadata:
            status = 'empty_or_invalid'
        else:
            status = 'unknown'
        
        return {
            'status': status,
            'total_lines': total_lines,
            'parsed_lines': parsed_lines,
            'conversation_rounds': conversation_rounds,
            'has_metadata': has_metadata,
            'has_actual_conversation': has_actual_conversation,
            'error': None,
            'file_size': os.path.getsize(file_path)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'total_lines': 0,
            'conversation_rounds': 0,
            'has_metadata': False,
            'has_actual_conversation': False,
            'error': str(e),
            'file_size': 0
        }

def analyze_batch_directory_corrected(batch_dir):
    """Analyze all JSONL files in a batch directory with corrected logic."""
    batch_path = Path(batch_dir)
    if not batch_path.exists():
        print(f"Directory {batch_dir} does not exist")
        return {}
    
    results = {}
    
    # Find all JSONL files recursively
    for jsonl_file in batch_path.rglob("*.jsonl"):
        relative_path = str(jsonl_file.relative_to(batch_path))
        results[relative_path] = analyze_jsonl_file_corrected(jsonl_file)
    
    return results

def extract_file_info(filename):
    """Extract information from filename."""
    parts = filename.split('_')
    info = {
        'tactic': 'unknown',
        'test_case': 'unknown',
        'model': 'unknown',
        'turn_type': 'unknown',
        'sample': 'unknown',
        'timestamp': 'unknown'
    }
    
    # Extract tactic (first part)
    if len(parts) > 0:
        info['tactic'] = parts[0]
    
    # Extract test case (second part)
    if len(parts) > 1:
        info['test_case'] = parts[1]
    
    # Find turn type and model
    for i, part in enumerate(parts):
        if part in ['single_turn', 'multi_turn']:
            info['turn_type'] = part
            # Model is usually the part before turn_type
            if i > 0:
                # Reconstruct model name from parts between test_case and turn_type
                model_parts = parts[2:i]
                if model_parts:
                    info['model'] = '_'.join(model_parts)
        elif part.startswith('sample'):
            info['sample'] = part
    
    return info

def main():
    parser = argparse.ArgumentParser(description='Corrected analysis of JSONL files for conversation data')
    parser.add_argument('--show-examples', action='store_true', 
                       help='Show examples of problematic files')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed analysis for each file')
    parser.add_argument('--line-count-threshold', type=int, default=2,
                       help='Files with lines <= this threshold are considered potentially empty')
    args = parser.parse_args()
    
    base_dir = Path("/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs")
    batches = ['batch6A', 'batch6B', 'batch6C']
    
    all_results = {}
    summary_stats = defaultdict(int)
    
    print("Corrected Analysis of JSONL files for conversation data...")
    print("=" * 60)
    
    for batch in batches:
        batch_dir = base_dir / batch
        print(f"\nAnalyzing {batch}...")
        
        batch_results = analyze_batch_directory_corrected(batch_dir)
        all_results[batch] = batch_results
        
        # Count by status
        status_counts = Counter()
        low_line_count_files = []
        
        for filename, result in batch_results.items():
            status_counts[result['status']] += 1
            
            # Files with very few lines might be problematic
            if result['total_lines'] <= args.line_count_threshold:
                low_line_count_files.append((filename, result['total_lines']))
        
        print(f"  Total files: {len(batch_results)}")
        print(f"  Complete conversation: {status_counts['complete_conversation']}")
        print(f"  Incomplete conversation: {status_counts['incomplete_conversation']}")
        print(f"  Metadata only: {status_counts['metadata_only']}")
        print(f"  Empty/Invalid: {status_counts['empty_or_invalid']}")
        print(f"  Errors: {status_counts['error']}")
        print(f"  Files with ≤{args.line_count_threshold} lines: {len(low_line_count_files)}")
        
        # Update summary stats
        summary_stats[f'{batch}_total'] = len(batch_results)
        summary_stats[f'{batch}_complete'] = status_counts['complete_conversation']
        summary_stats[f'{batch}_incomplete'] = status_counts['incomplete_conversation']
        summary_stats[f'{batch}_metadata_only'] = status_counts['metadata_only']
        summary_stats[f'{batch}_empty_invalid'] = status_counts['empty_or_invalid']
        summary_stats[f'{batch}_errors'] = status_counts['error']
        summary_stats[f'{batch}_low_lines'] = len(low_line_count_files)
        
        # Show examples if requested
        if args.show_examples:
            if low_line_count_files:
                print(f"\n  Files with ≤{args.line_count_threshold} lines in {batch}:")
                for filename, line_count in sorted(low_line_count_files)[:5]:
                    print(f"    {filename} ({line_count} lines)")
                if len(low_line_count_files) > 5:
                    print(f"    ... and {len(low_line_count_files) - 5} more")
            
            # Show metadata-only files
            metadata_only_files = [f for f, r in batch_results.items() if r['status'] == 'metadata_only']
            if metadata_only_files:
                print(f"\n  Metadata-only files in {batch}:")
                for filename in metadata_only_files[:3]:
                    print(f"    {filename}")
                if len(metadata_only_files) > 3:
                    print(f"    ... and {len(metadata_only_files) - 3} more")
    
    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    
    total_files = sum(summary_stats[f'{batch}_total'] for batch in batches)
    total_complete = sum(summary_stats[f'{batch}_complete'] for batch in batches)
    total_incomplete = sum(summary_stats[f'{batch}_incomplete'] for batch in batches)
    total_metadata_only = sum(summary_stats[f'{batch}_metadata_only'] for batch in batches)
    total_empty_invalid = sum(summary_stats[f'{batch}_empty_invalid'] for batch in batches)
    total_errors = sum(summary_stats[f'{batch}_errors'] for batch in batches)
    total_low_lines = sum(summary_stats[f'{batch}_low_lines'] for batch in batches)
    
    print(f"Total files analyzed: {total_files}")
    print(f"Complete conversations: {total_complete} ({total_complete/total_files*100:.1f}%)")
    print(f"Incomplete conversations: {total_incomplete} ({total_incomplete/total_files*100:.1f}%)")
    print(f"Metadata only: {total_metadata_only} ({total_metadata_only/total_files*100:.1f}%)")
    print(f"Empty/Invalid files: {total_empty_invalid} ({total_empty_invalid/total_files*100:.1f}%)")
    print(f"Files with errors: {total_errors} ({total_errors/total_files*100:.1f}%)")
    print(f"Files with ≤{args.line_count_threshold} lines: {total_low_lines} ({total_low_lines/total_files*100:.1f}%)")
    
    # Analysis of conversation rounds distribution
    print("\n" + "=" * 60)
    print("CONVERSATION ROUNDS DISTRIBUTION")
    print("=" * 60)
    
    rounds_distribution = Counter()
    for batch, batch_results in all_results.items():
        for filename, result in batch_results.items():
            rounds_distribution[result['conversation_rounds']] += 1
    
    print("Files by number of conversation rounds:")
    for rounds in sorted(rounds_distribution.keys()):
        count = rounds_distribution[rounds]
        print(f"  {rounds} rounds: {count} files ({count/total_files*100:.1f}%)")

if __name__ == "__main__":
    main()