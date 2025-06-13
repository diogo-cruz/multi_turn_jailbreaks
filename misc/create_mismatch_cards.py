#!/usr/bin/env python3
"""
Create detailed mismatch cards showing experiment conditions for all evaluation mismatches
"""

import os
import json
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def extract_detailed_info(file_path):
    """Extract detailed information from a JSONL file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        config = None
        goal_achieved = None
        rounds = []
        non_round_entries = []
        all_scores = []
        round_scores = []
        non_round_scores = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Extract config (first line usually)
                if 'target_model' in data and 'jailbreak_tactic' in data and config is None:
                    config = data
                
                # Check for goal_achieved
                if 'goal_achieved' in data:
                    goal_achieved = data['goal_achieved']
                
                # Separate rounds vs non-round entries
                if 'round' in data:
                    rounds.append({
                        'line_num': line_num,
                        'round': data['round'],
                        'score': data.get('score'),
                        'user': data.get('user', '')[:100] + '...' if len(data.get('user', '')) > 100 else data.get('user', ''),
                        'assistant': data.get('assistant', '')[:200] + '...' if len(data.get('assistant', '')) > 200 else data.get('assistant', ''),
                        'has_rationale': 'rationale' in data,
                        'has_token_usage': 'token_usage' in data,
                    })
                    if 'score' in data:
                        round_scores.append(data['score'])
                        all_scores.append(('round', data['round'], data['score']))
                else:
                    # Non-round entry
                    if 'score' in data:
                        non_round_entry = {
                            'line_num': line_num,
                            'score': data['score'],
                            'type': 'unknown',
                            'keys': list(data.keys()),
                            'has_goal': 'goal' in data,
                            'has_target_response': 'target_response' in data,
                            'has_tactic_prompt': 'tactic_prompt' in data,
                            'has_metadata': 'metadata' in data,
                            'sample_content': str(data)[:300] + '...' if len(str(data)) > 300 else str(data)
                        }
                        non_round_entries.append(non_round_entry)
                        non_round_scores.append(data['score'])
                        all_scores.append(('non_round', line_num, data['score']))
                        
            except json.JSONDecodeError as e:
                continue
        
        # Calculate relative path
        base_path = Path("../clean_results/final_runs")
        try:
            rel_path = Path(file_path).relative_to(base_path)
            subdirectory = rel_path.parts[0] if rel_path.parts else "unknown"
            subpath = "/".join(rel_path.parts[1:]) if len(rel_path.parts) > 1 else ""
        except ValueError:
            subdirectory = "unknown"
            subpath = str(file_path)
        
        # Analyze scores
        has_score_1_in_rounds = any(score == 1.0 or score == 1 for score in round_scores if score not in ['refused', None])
        has_score_1_in_non_rounds = any(score == 1.0 or score == 1 for score in non_round_scores if score not in ['refused', None])
        
        return {
            # File info
            'file_path': str(file_path),
            'subdirectory': subdirectory,
            'subpath': subpath,
            'filename': Path(file_path).name,
            
            # Config info
            'target_model': config.get('target_model', 'unknown') if config else 'unknown',
            'jailbreak_tactic': config.get('jailbreak_tactic', 'unknown') if config else 'unknown',
            'test_case': config.get('test_case', 'unknown') if config else 'unknown',
            'turn_type': config.get('turn_type', 'unknown') if config else 'unknown',
            'target_temp': config.get('target_temp', 'unknown') if config else 'unknown',
            'attacker_model': config.get('attacker_model', 'unknown') if config else 'unknown',
            'evaluator_model': config.get('evaluator_model', 'unknown') if config else 'unknown',
            'timestamp': config.get('timestamp', 'unknown') if config else 'unknown',
            'category': config.get('category', 'unknown') if config else 'unknown',
            'max_rounds': config.get('max_rounds', 'unknown') if config else 'unknown',
            
            # Evaluation results
            'goal_achieved': goal_achieved,
            'num_rounds': len(rounds),
            'num_non_round_entries': len(non_round_entries),
            'total_lines': len(lines),
            
            # Score analysis
            'round_scores': round_scores,
            'non_round_scores': non_round_scores,
            'has_score_1_in_rounds': has_score_1_in_rounds,
            'has_score_1_in_non_rounds': has_score_1_in_non_rounds,
            'unique_round_scores': list(set(round_scores)),
            'unique_non_round_scores': list(set(non_round_scores)),
            
            # Mismatch classification
            'mismatch_type_1': goal_achieved is True and not has_score_1_in_rounds,
            'mismatch_type_2': goal_achieved is True and not (has_score_1_in_rounds or has_score_1_in_non_rounds),
            
            # Detailed data for analysis
            'rounds_summary': rounds,
            'non_round_summary': non_round_entries,
            'all_scores_timeline': all_scores,
        }
        
    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'mismatch_type_1': False,
            'mismatch_type_2': False
        }

def create_mismatch_cards():
    """Create detailed cards for all mismatch cases"""
    base_dir = "../clean_results/final_runs"
    base_path = Path(base_dir)
    
    print("Scanning for mismatch files...")
    mismatch_files = []
    total_files = 0
    
    for jsonl_file in base_path.rglob("*.jsonl"):
        total_files += 1
        if total_files % 1000 == 0:
            print(f"  Processed {total_files} files...")
        
        result = extract_detailed_info(jsonl_file)
        if result.get('mismatch_type_1', False):
            mismatch_files.append(result)
    
    print(f"\nFound {len(mismatch_files)} mismatch files out of {total_files} total files")
    
    # Create CSV output
    csv_filename = "mismatch_cards_detailed.csv"
    print(f"Creating detailed CSV: {csv_filename}")
    
    fieldnames = [
        # File identification
        'subdirectory', 'filename', 'subpath',
        
        # Experiment config
        'target_model', 'jailbreak_tactic', 'test_case', 'turn_type', 'target_temp',
        'attacker_model', 'evaluator_model', 'timestamp', 'category', 'max_rounds',
        
        # Results
        'goal_achieved', 'num_rounds', 'num_non_round_entries', 'total_lines',
        
        # Score analysis
        'has_score_1_in_rounds', 'has_score_1_in_non_rounds',
        'mismatch_type_1', 'mismatch_type_2',
        'round_scores', 'non_round_scores',
        'unique_round_scores', 'unique_non_round_scores',
        
        # Sample data for inspection
        'first_round_score', 'last_round_score', 'first_non_round_score',
        'sample_non_round_entry_keys', 'file_path'
    ]
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in mismatch_files:
            # Prepare row data
            row = {}
            for field in fieldnames:
                if field in result:
                    row[field] = result[field]
                elif field == 'first_round_score':
                    row[field] = result['round_scores'][0] if result['round_scores'] else None
                elif field == 'last_round_score':
                    row[field] = result['round_scores'][-1] if result['round_scores'] else None
                elif field == 'first_non_round_score':
                    row[field] = result['non_round_scores'][0] if result['non_round_scores'] else None
                elif field == 'sample_non_round_entry_keys':
                    if result['non_round_summary']:
                        row[field] = str(result['non_round_summary'][0]['keys'])
                    else:
                        row[field] = None
                else:
                    row[field] = None
            
            writer.writerow(row)
    
    # Create summary analysis
    print("\n" + "=" * 80)
    print("MISMATCH PATTERN ANALYSIS")
    print("=" * 80)
    
    # Group by key factors
    by_subdirectory = defaultdict(int)
    by_model = defaultdict(int)
    by_tactic = defaultdict(int)
    by_evaluator = defaultdict(int)
    by_turn_type = defaultdict(int)
    by_non_round_score_presence = defaultdict(int)
    
    for result in mismatch_files:
        by_subdirectory[result['subdirectory']] += 1
        by_model[result['target_model']] += 1
        by_tactic[result['jailbreak_tactic']] += 1
        by_evaluator[result['evaluator_model']] += 1
        by_turn_type[result['turn_type']] += 1
        by_non_round_score_presence[bool(result['has_score_1_in_non_rounds'])] += 1
    
    print(f"\nMismatches by Subdirectory:")
    for subdir, count in sorted(by_subdirectory.items(), key=lambda x: x[1], reverse=True):
        print(f"  {subdir}: {count}")
    
    print(f"\nTop 10 Target Models:")
    for model, count in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {model}: {count}")
    
    print(f"\nMismatches by Tactic:")
    for tactic, count in sorted(by_tactic.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tactic}: {count}")
    
    print(f"\nMismatches by Evaluator Model:")
    for evaluator, count in sorted(by_evaluator.items(), key=lambda x: x[1], reverse=True):
        print(f"  {evaluator}: {count}")
    
    print(f"\nMismatches by Turn Type:")
    for turn_type, count in sorted(by_turn_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {turn_type}: {count}")
    
    print(f"\nHas Score=1.0 in Non-Round Entries:")
    for has_score, count in by_non_round_score_presence.items():
        print(f"  {has_score}: {count}")
    
    # Analyze timestamp patterns
    print(f"\nTimestamp Analysis:")
    timestamps = [result['timestamp'] for result in mismatch_files if result['timestamp'] != 'unknown']
    if timestamps:
        print(f"  Earliest: {min(timestamps)}")
        print(f"  Latest: {max(timestamps)}")
        print(f"  Sample timestamps: {timestamps[:5]}")
    
    # Show sample detailed entries
    print("\n" + "=" * 80)
    print("SAMPLE MISMATCH CASES FOR DETAILED INSPECTION")
    print("=" * 80)
    
    # Show examples from different categories
    examples_shown = 0
    for subdir in ['batch3A', 'batch_thinking', 'batch_4H']:
        subdir_files = [f for f in mismatch_files if f['subdirectory'] == subdir]
        if subdir_files and examples_shown < 3:
            example = subdir_files[0]
            print(f"\n--- Example from {subdir} ---")
            print(f"File: {example['filename']}")
            print(f"Model: {example['target_model']}")
            print(f"Tactic: {example['jailbreak_tactic']}")
            print(f"Rounds: {example['num_rounds']}, Non-round entries: {example['num_non_round_entries']}")
            print(f"Round scores: {example['round_scores']}")
            print(f"Non-round scores: {example['non_round_scores']}")
            print(f"Has score=1 in non-rounds: {example['has_score_1_in_non_rounds']}")
            
            if example['non_round_summary']:
                print(f"Sample non-round entry keys: {example['non_round_summary'][0]['keys']}")
                print(f"Sample content: {example['non_round_summary'][0]['sample_content'][:200]}...")
            
            examples_shown += 1
    
    print(f"\n✅ Analysis complete! Check '{csv_filename}' for detailed data.")
    print(f"Total mismatch files analyzed: {len(mismatch_files)}")

if __name__ == "__main__":
    create_mismatch_cards()