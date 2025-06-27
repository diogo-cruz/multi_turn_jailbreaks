#!/usr/bin/env python3
"""
Analyze JSONL files in batch6A, batch6B, and batch6C directories to find files 
that contain only metadata but no actual conversation rounds.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
import argparse

def count_lines_in_file(file_path):
    """Count the number of lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def analyze_jsonl_file(file_path):
    """
    Analyze a JSONL file to determine if it contains only metadata or actual conversation rounds.
    Returns a dict with analysis results.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # If file has 0 lines, it's empty
        if total_lines == 0:
            return {
                'status': 'empty',
                'total_lines': 0,
                'conversation_rounds': 0,
                'has_metadata': False,
                'error': None,
                'file_size': os.path.getsize(file_path)
            }
        
        conversation_rounds = 0
        has_metadata = False
        parsed_lines = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                parsed_lines += 1
                
                # Check if this line contains conversation data
                if 'conversation' in data:
                    conversation = data['conversation']
                    if isinstance(conversation, list) and len(conversation) > 0:
                        conversation_rounds += len(conversation)
                elif 'rounds' in data:
                    rounds = data['rounds']
                    if isinstance(rounds, list) and len(rounds) > 0:
                        conversation_rounds += len(rounds)
                
                # Check if this looks like metadata
                metadata_fields = ['model', 'test_case', 'tactic', 'timestamp', 'sample_id', 'turn_type']
                if any(field in data for field in metadata_fields):
                    has_metadata = True
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error in {file_path} line {line_num}: {e}")
                continue
        
        # Determine status
        if conversation_rounds == 0 and has_metadata:
            status = 'metadata_only'
        elif conversation_rounds == 0 and not has_metadata:
            status = 'empty_or_invalid'
        elif conversation_rounds > 0:
            status = 'has_conversation'
        else:
            status = 'unknown'
        
        return {
            'status': status,
            'total_lines': total_lines,
            'parsed_lines': parsed_lines,
            'conversation_rounds': conversation_rounds,
            'has_metadata': has_metadata,
            'error': None,
            'file_size': os.path.getsize(file_path)
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'total_lines': 0,
            'conversation_rounds': 0,
            'has_metadata': False,
            'error': str(e),
            'file_size': 0
        }

def analyze_batch_directory(batch_dir):
    """Analyze all JSONL files in a batch directory."""
    batch_path = Path(batch_dir)
    if not batch_path.exists():
        print(f"Directory {batch_dir} does not exist")
        return {}
    
    results = {}
    
    # Find all JSONL files recursively
    for jsonl_file in batch_path.rglob("*.jsonl"):
        relative_path = str(jsonl_file.relative_to(batch_path))
        results[relative_path] = analyze_jsonl_file(jsonl_file)
    
    return results

def extract_file_info(filename):
    """Extract information from filename."""
    parts = filename.split('_')
    info = {
        'tactic': parts[0] if len(parts) > 0 else 'unknown',
        'test_case': parts[1] if len(parts) > 1 else 'unknown',
        'model': 'unknown',
        'turn_type': 'unknown',
        'sample': 'unknown',
        'timestamp': 'unknown'
    }
    
    # Try to extract model, turn_type, sample, and timestamp
    for i, part in enumerate(parts):
        if part in ['single_turn', 'multi_turn']:
            info['turn_type'] = part
            # Model is usually the part before turn_type
            if i > 0:
                info['model'] = parts[i-1]
        elif part.startswith('sample'):
            info['sample'] = part
        elif len(part) == 4 and part.isdigit():  # Year
            # Timestamp parts
            if i + 5 < len(parts):
                info['timestamp'] = '_'.join(parts[i:i+6])
    
    return info

def main():
    parser = argparse.ArgumentParser(description='Analyze JSONL files for empty conversations')
    parser.add_argument('--show-examples', action='store_true', 
                       help='Show examples of empty files')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed analysis for each file')
    args = parser.parse_args()
    
    base_dir = Path("/home/dcruz/multi_turn_jailbreaks/clean_results/final_runs")
    batches = ['batch6A', 'batch6B', 'batch6C']
    
    all_results = {}
    summary_stats = defaultdict(int)
    
    print("Analyzing JSONL files for empty conversations...")
    print("=" * 60)
    
    for batch in batches:
        batch_dir = base_dir / batch
        print(f"\nAnalyzing {batch}...")
        
        batch_results = analyze_batch_directory(batch_dir)
        all_results[batch] = batch_results
        
        # Count by status
        status_counts = Counter()
        empty_files = []
        
        for filename, result in batch_results.items():
            status_counts[result['status']] += 1
            
            if result['status'] == 'metadata_only':
                empty_files.append(filename)
        
        print(f"  Total files: {len(batch_results)}")
        print(f"  Metadata only: {status_counts['metadata_only']}")
        print(f"  Has conversation: {status_counts['has_conversation']}")
        print(f"  Empty/Invalid: {status_counts['empty_or_invalid']}")
        print(f"  Errors: {status_counts['error']}")
        
        # Update summary stats
        summary_stats[f'{batch}_total'] = len(batch_results)
        summary_stats[f'{batch}_metadata_only'] = status_counts['metadata_only']
        summary_stats[f'{batch}_has_conversation'] = status_counts['has_conversation']
        summary_stats[f'{batch}_empty_invalid'] = status_counts['empty_or_invalid']
        summary_stats[f'{batch}_errors'] = status_counts['error']
        
        # Show examples if requested
        if args.show_examples and empty_files:
            print(f"\n  Examples of metadata-only files in {batch}:")
            for filename in empty_files[:5]:  # Show first 5
                print(f"    {filename}")
            if len(empty_files) > 5:
                print(f"    ... and {len(empty_files) - 5} more")
    
    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    
    total_files = sum(summary_stats[f'{batch}_total'] for batch in batches)
    total_metadata_only = sum(summary_stats[f'{batch}_metadata_only'] for batch in batches)
    total_has_conversation = sum(summary_stats[f'{batch}_has_conversation'] for batch in batches)
    total_empty_invalid = sum(summary_stats[f'{batch}_empty_invalid'] for batch in batches)
    total_errors = sum(summary_stats[f'{batch}_errors'] for batch in batches)
    
    print(f"Total files analyzed: {total_files}")
    print(f"Files with metadata only: {total_metadata_only} ({total_metadata_only/total_files*100:.1f}%)")
    print(f"Files with conversation: {total_has_conversation} ({total_has_conversation/total_files*100:.1f}%)")
    print(f"Empty/Invalid files: {total_empty_invalid} ({total_empty_invalid/total_files*100:.1f}%)")
    print(f"Files with errors: {total_errors} ({total_errors/total_files*100:.1f}%)")
    
    # Pattern analysis for metadata-only files
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS FOR METADATA-ONLY FILES")
    print("=" * 60)
    
    metadata_only_files = []
    for batch, batch_results in all_results.items():
        for filename, result in batch_results.items():
            if result['status'] == 'metadata_only':
                file_info = extract_file_info(filename)
                file_info['batch'] = batch
                file_info['filename'] = filename
                metadata_only_files.append(file_info)
    
    if metadata_only_files:
        # Analyze patterns
        model_counts = Counter(f['model'] for f in metadata_only_files)
        tactic_counts = Counter(f['tactic'] for f in metadata_only_files)
        test_case_counts = Counter(f['test_case'] for f in metadata_only_files)
        turn_type_counts = Counter(f['turn_type'] for f in metadata_only_files)
        batch_counts = Counter(f['batch'] for f in metadata_only_files)
        
        print(f"Total metadata-only files: {len(metadata_only_files)}")
        print(f"\nBy Batch:")
        for batch, count in batch_counts.most_common():
            print(f"  {batch}: {count}")
        
        print(f"\nBy Model:")
        for model, count in model_counts.most_common():
            print(f"  {model}: {count}")
        
        print(f"\nBy Tactic:")
        for tactic, count in tactic_counts.most_common():
            print(f"  {tactic}: {count}")
        
        print(f"\nBy Test Case:")
        for test_case, count in test_case_counts.most_common():
            print(f"  {test_case}: {count}")
        
        print(f"\nBy Turn Type:")
        for turn_type, count in turn_type_counts.most_common():
            print(f"  {turn_type}: {count}")
    
    # Show detailed analysis if requested
    if args.detailed:
        print("\n" + "=" * 60)
        print("DETAILED ANALYSIS")
        print("=" * 60)
        
        for batch, batch_results in all_results.items():
            print(f"\n{batch}:")
            for filename, result in batch_results.items():
                if result['status'] == 'metadata_only':
                    print(f"  {filename}")
                    print(f"    Lines: {result['total_lines']}, Size: {result['file_size']} bytes")

if __name__ == "__main__":
    main()