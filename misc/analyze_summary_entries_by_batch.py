#!/usr/bin/env python3
"""
Analyze which batches have summary/output_data entries (non-round entries with scores)
"""

import os
import json
from pathlib import Path
from collections import defaultdict

def analyze_file_structure(file_path):
    """Analyze the structure of a JSONL file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        rounds = []
        non_round_entries = []
        goal_achieved = None
        config = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Check for config (usually first line)
                if 'target_model' in data and 'jailbreak_tactic' in data and config is None:
                    config = data
                
                # Check for goal_achieved
                if 'goal_achieved' in data:
                    goal_achieved = data['goal_achieved']
                
                # Check for round vs non-round entries
                if 'round' in data:
                    rounds.append({
                        'round': data['round'],
                        'score': data.get('score'),
                        'has_user': 'user' in data,
                        'has_assistant': 'assistant' in data
                    })
                elif 'score' in data:
                    # Non-round entry with score (potential summary entry)
                    non_round_entries.append({
                        'line_num': line_num,
                        'score': data['score'],
                        'has_goal': 'goal' in data,
                        'has_target_response': 'target_response' in data,
                        'has_tactic_prompt': 'tactic_prompt' in data,
                        'has_metadata': 'metadata' in data,
                        'keys': list(data.keys())
                    })
                        
            except json.JSONDecodeError:
                continue
        
        return {
            'file_path': str(file_path),
            'config': config,
            'num_rounds': len(rounds),
            'num_non_round_entries': len(non_round_entries),
            'has_summary_entries': len(non_round_entries) > 0,
            'goal_achieved': goal_achieved,
            'round_scores': [r['score'] for r in rounds],
            'non_round_scores': [e['score'] for e in non_round_entries],
            'summary_entry_example': non_round_entries[0] if non_round_entries else None
        }
        
    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'has_summary_entries': False
        }

def analyze_by_batch():
    """Analyze file structures by batch directory"""
    base_dir = "../clean_results/final_runs"
    base_path = Path(base_dir)
    
    batch_results = defaultdict(lambda: {
        'total_files': 0,
        'files_with_summary': 0,
        'files_without_summary': 0,
        'sample_files': [],
        'summary_entry_types': defaultdict(int)
    })
    
    print("Scanning all batches...")
    
    for jsonl_file in base_path.rglob("*.jsonl"):
        # Get batch directory
        try:
            relative_path = jsonl_file.relative_to(base_path)
            batch = relative_path.parts[0] if relative_path.parts else "unknown"
        except ValueError:
            batch = "unknown"
        
        result = analyze_file_structure(jsonl_file)
        
        batch_results[batch]['total_files'] += 1
        
        if result.get('has_summary_entries', False):
            batch_results[batch]['files_with_summary'] += 1
            
            # Analyze summary entry types
            example = result.get('summary_entry_example')
            if example and example.get('keys'):
                key_signature = tuple(sorted(example['keys']))
                batch_results[batch]['summary_entry_types'][key_signature] += 1
        else:
            batch_results[batch]['files_without_summary'] += 1
        
        # Keep some samples for detailed inspection
        if len(batch_results[batch]['sample_files']) < 3:
            batch_results[batch]['sample_files'].append(result)
    
    return batch_results

def main():
    print("=" * 80)
    print("SUMMARY ENTRY ANALYSIS BY BATCH")
    print("=" * 80)
    
    batch_results = analyze_by_batch()
    
    # Sort batches by name
    sorted_batches = sorted(batch_results.keys())
    
    print(f"\n{'Batch':<20} {'Total':<8} {'With Summary':<12} {'Without Summary':<15} {'% With Summary':<15}")
    print("-" * 80)
    
    for batch in sorted_batches:
        data = batch_results[batch]
        total = data['total_files']
        with_summary = data['files_with_summary']
        without_summary = data['files_without_summary']
        pct_with = (with_summary / total * 100) if total > 0 else 0
        
        print(f"{batch:<20} {total:<8} {with_summary:<12} {without_summary:<15} {pct_with:<14.1f}%")
    
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80)
    
    for batch in sorted_batches:
        data = batch_results[batch]
        
        if data['files_with_summary'] > 0:
            print(f"\n--- {batch} ---")
            print(f"Summary entries found in {data['files_with_summary']}/{data['total_files']} files")
            
            # Show summary entry types
            if data['summary_entry_types']:
                print("Summary entry key patterns:")
                for key_sig, count in sorted(data['summary_entry_types'].items(), key=lambda x: x[1], reverse=True):
                    # Show first few keys to identify the pattern
                    key_preview = list(key_sig)[:5]
                    print(f"  {count} files: {key_preview}... ({len(key_sig)} total keys)")
            
            # Show a sample file
            sample_with_summary = None
            for sample in data['sample_files']:
                if sample.get('has_summary_entries'):
                    sample_with_summary = sample
                    break
            
            if sample_with_summary:
                print(f"Sample file: {Path(sample_with_summary['file_path']).name}")
                print(f"  Rounds: {sample_with_summary['num_rounds']}")
                print(f"  Summary entries: {sample_with_summary['num_non_round_entries']}")
                print(f"  Round scores: {sample_with_summary['round_scores']}")
                print(f"  Summary scores: {sample_with_summary['non_round_scores']}")
        
        elif data['total_files'] > 0:
            print(f"\n--- {batch} ---")
            print(f"NO summary entries found (clean format)")
            
            # Show a sample clean file
            sample = data['sample_files'][0] if data['sample_files'] else None
            if sample:
                print(f"Sample file: {Path(sample['file_path']).name}")
                print(f"  Rounds: {sample['num_rounds']}")
                print(f"  Round scores: {sample['round_scores']}")
    
    # Timeline analysis
    print("\n" + "=" * 80)
    print("TIMELINE ANALYSIS")
    print("=" * 80)
    print("Batches WITHOUT summary entries (clean format):")
    for batch in sorted_batches:
        if batch_results[batch]['files_with_summary'] == 0 and batch_results[batch]['total_files'] > 0:
            print(f"  {batch}")
    
    print("\nBatches WITH summary entries (problematic format):")
    for batch in sorted_batches:
        if batch_results[batch]['files_with_summary'] > 0:
            pct = batch_results[batch]['files_with_summary'] / batch_results[batch]['total_files'] * 100
            print(f"  {batch}: {pct:.1f}% of files")

if __name__ == "__main__":
    main()