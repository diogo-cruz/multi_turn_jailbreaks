#!/usr/bin/env python3
"""
Analyze evaluation mismatches (goal_achieved: true but no score: 1.0) by subdirectory
"""

import os
import json
from pathlib import Path
from collections import defaultdict

def analyze_file(file_path):
    """Analyze a single JSONL file for evaluation consistency"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        goal_achieved = None
        has_score_1_in_rounds = False
        has_any_score_1 = False
        config = None
        rounds = []
        all_entries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                all_entries.append(data)
                
                # Check for config (first line)
                if 'target_model' in data and 'jailbreak_tactic' in data and config is None:
                    config = data
                
                # Check for goal_achieved
                if 'goal_achieved' in data:
                    goal_achieved = data['goal_achieved']
                
                # Check for conversation rounds with scores
                if 'round' in data:
                    rounds.append(data)
                    score = data.get('score')
                    if score == 1.0 or score == 1:
                        has_score_1_in_rounds = True
                
                # Check for ANY score = 1.0 (including non-round entries)
                if 'score' in data and (data['score'] == 1.0 or data['score'] == 1):
                    has_any_score_1 = True
                        
            except json.JSONDecodeError:
                continue
        
        return {
            'file_path': str(file_path),
            'config': config,
            'goal_achieved': goal_achieved,
            'has_score_1_in_rounds': has_score_1_in_rounds,
            'has_any_score_1': has_any_score_1,
            'num_rounds': len(rounds),
            'num_entries': len(all_entries),
            'mismatch_type_1': goal_achieved is True and not has_score_1_in_rounds,  # goal=true but no score=1 in rounds
            'mismatch_type_2': goal_achieved is True and not has_any_score_1,        # goal=true but no score=1 anywhere
        }
        
    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'mismatch_type_1': False,
            'mismatch_type_2': False
        }

def scan_directory_recursive(base_path):
    """Scan all JSONL files recursively and organize by subdirectory"""
    base_path = Path(base_path)
    results_by_subdir = defaultdict(list)
    
    for jsonl_file in base_path.rglob("*.jsonl"):
        # Get the immediate subdirectory under final_runs
        try:
            relative_path = jsonl_file.relative_to(base_path)
            subdir = relative_path.parts[0] if relative_path.parts else "root"
        except ValueError:
            subdir = "unknown"
        
        result = analyze_file(jsonl_file)
        results_by_subdir[subdir].append(result)
    
    return results_by_subdir

def main():
    base_dir = "../clean_results/final_runs"
    
    print("=" * 100)
    print("EVALUATION MISMATCH ANALYSIS BY SUBDIRECTORY")
    print("=" * 100)
    print("Mismatch Type 1: goal_achieved: true but no score=1.0 in conversation rounds")
    print("Mismatch Type 2: goal_achieved: true but no score=1.0 anywhere in file")
    print("=" * 100)
    
    results_by_subdir = scan_directory_recursive(base_dir)
    
    # Summary table
    print(f"\n{'Subdirectory':<25} {'Total':<8} {'Goal=True':<10} {'Mismatch1':<10} {'Mismatch2':<10} {'%Mismatch1':<12} {'%Mismatch2':<12}")
    print("-" * 100)
    
    total_files = 0
    total_goal_true = 0
    total_mismatch_1 = 0
    total_mismatch_2 = 0
    
    for subdir in sorted(results_by_subdir.keys()):
        results = results_by_subdir[subdir]
        
        num_files = len(results)
        num_goal_true = len([r for r in results if r.get('goal_achieved') is True])
        num_mismatch_1 = len([r for r in results if r.get('mismatch_type_1', False)])
        num_mismatch_2 = len([r for r in results if r.get('mismatch_type_2', False)])
        
        pct_mismatch_1 = (num_mismatch_1 / num_goal_true * 100) if num_goal_true > 0 else 0
        pct_mismatch_2 = (num_mismatch_2 / num_goal_true * 100) if num_goal_true > 0 else 0
        
        print(f"{subdir:<25} {num_files:<8} {num_goal_true:<10} {num_mismatch_1:<10} {num_mismatch_2:<10} {pct_mismatch_1:<11.1f}% {pct_mismatch_2:<11.1f}%")
        
        total_files += num_files
        total_goal_true += num_goal_true
        total_mismatch_1 += num_mismatch_1
        total_mismatch_2 += num_mismatch_2
    
    # Overall totals
    print("-" * 100)
    total_pct_1 = (total_mismatch_1 / total_goal_true * 100) if total_goal_true > 0 else 0
    total_pct_2 = (total_mismatch_2 / total_goal_true * 100) if total_goal_true > 0 else 0
    print(f"{'TOTAL':<25} {total_files:<8} {total_goal_true:<10} {total_mismatch_1:<10} {total_mismatch_2:<10} {total_pct_1:<11.1f}% {total_pct_2:<11.1f}%")
    
    # Detailed analysis for subdirectories with high mismatch rates
    print("\n" + "=" * 100)
    print("DETAILED ANALYSIS FOR HIGH-MISMATCH SUBDIRECTORIES")
    print("=" * 100)
    
    for subdir in sorted(results_by_subdir.keys()):
        results = results_by_subdir[subdir]
        num_goal_true = len([r for r in results if r.get('goal_achieved') is True])
        num_mismatch_1 = len([r for r in results if r.get('mismatch_type_1', False)])
        
        if num_goal_true > 0:
            pct_mismatch_1 = (num_mismatch_1 / num_goal_true * 100)
            
            if pct_mismatch_1 > 20:  # Show details for subdirs with >20% mismatch rate
                print(f"\n--- {subdir} (Mismatch Rate: {pct_mismatch_1:.1f}%) ---")
                
                # Analyze by tactic and model
                mismatch_files = [r for r in results if r.get('mismatch_type_1', False)]
                
                # Group by tactic
                by_tactic = defaultdict(int)
                by_model = defaultdict(int)
                
                for file_result in mismatch_files:
                    config = file_result.get('config', {})
                    tactic = config.get('jailbreak_tactic', 'unknown')
                    model = config.get('target_model', 'unknown')
                    
                    by_tactic[tactic] += 1
                    by_model[model] += 1
                
                print(f"  Mismatches by tactic:")
                for tactic, count in sorted(by_tactic.items(), key=lambda x: x[1], reverse=True):
                    print(f"    {tactic}: {count}")
                
                print(f"  Mismatches by model:")
                for model, count in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:  # Top 5
                    print(f"    {model}: {count}")
    
    # Analysis of mismatch type differences
    print("\n" + "=" * 100)
    print("MISMATCH TYPE COMPARISON")
    print("=" * 100)
    print("Files where Type1 != Type2 (goal=true, no score=1 in rounds, but score=1 exists elsewhere)")
    
    type_diff_count = 0
    for subdir, results in results_by_subdir.items():
        subdir_diff = 0
        for result in results:
            if result.get('mismatch_type_1', False) and not result.get('mismatch_type_2', False):
                subdir_diff += 1
                type_diff_count += 1
        
        if subdir_diff > 0:
            print(f"{subdir}: {subdir_diff} files")
    
    print(f"\nTotal files with Type1 but not Type2: {type_diff_count}")
    print("(These files have goal_achieved=true, no score=1 in rounds, but score=1 exists in non-round entries)")

if __name__ == "__main__":
    main()