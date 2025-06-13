#!/usr/bin/env python3
"""
Script to find files with goal_achieved: true but no score = 1.0
This helps identify inconsistencies in the evaluation methodology.
"""

import os
import json
from pathlib import Path

def analyze_file(file_path):
    """Analyze a single JSONL file for goal_achieved vs score = 1.0 mismatch"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        goal_achieved = None
        has_score_1 = False
        all_scores = []
        turns = []
        config = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Check for config (first line)
                if 'target_model' in data and 'jailbreak_tactic' in data and config is None:
                    config = data
                
                # Check for goal_achieved
                if 'goal_achieved' in data:
                    goal_achieved = data['goal_achieved']
                
                # Check for conversation turns with scores
                if 'round' in data and 'score' in data:
                    score = data['score']
                    all_scores.append(score)
                    turns.append({
                        'round': data['round'],
                        'score': score,
                        'user': data.get('user', '')[:100] + '...' if len(data.get('user', '')) > 100 else data.get('user', ''),
                        'assistant': data.get('assistant', '')[:100] + '...' if len(data.get('assistant', '')) > 100 else data.get('assistant', '')
                    })
                    
                    if score == 1.0 or score == 1:
                        has_score_1 = True
                        
            except json.JSONDecodeError:
                continue
        
        return {
            'file_path': str(file_path),
            'config': config,
            'goal_achieved': goal_achieved,
            'has_score_1': has_score_1,
            'all_scores': all_scores,
            'turns': turns,
            'mismatch': goal_achieved is True and not has_score_1
        }
        
    except Exception as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'mismatch': False
        }

def scan_directory(base_path):
    """Scan all JSONL files in the directory recursively"""
    base_path = Path(base_path)
    results = []
    
    print(f"Scanning directory: {base_path}")
    
    for jsonl_file in base_path.rglob("*.jsonl"):
        result = analyze_file(jsonl_file)
        results.append(result)
    
    return results

def main():
    # Scan the clean_results/final_runs directory
    base_dir = "../clean_results/final_runs"
    
    print("=" * 80)
    print("ANALYZING FILES WITH goal_achieved: true BUT NO score = 1.0")
    print("=" * 80)
    
    results = scan_directory(base_dir)
    
    # Filter for mismatches
    mismatches = [r for r in results if r.get('mismatch', False)]
    
    print(f"\nTotal files analyzed: {len(results)}")
    print(f"Files with goal_achieved: true: {len([r for r in results if r.get('goal_achieved') is True])}")
    print(f"Files with score = 1.0: {len([r for r in results if r.get('has_score_1', False)])}")
    print(f"MISMATCHES (goal_achieved: true but no score = 1.0): {len(mismatches)}")
    
    if mismatches:
        print("\n" + "=" * 80)
        print("DETAILED MISMATCH ANALYSIS")
        print("=" * 80)
        
        for i, mismatch in enumerate(mismatches[:10]):  # Show first 10 mismatches
            print(f"\n--- MISMATCH #{i+1} ---")
            print(f"File: {mismatch['file_path']}")
            
            if mismatch.get('config'):
                config = mismatch['config']
                print(f"Model: {config.get('target_model', 'Unknown')}")
                print(f"Tactic: {config.get('jailbreak_tactic', 'Unknown')}")
                print(f"Test Case: {config.get('test_case', 'Unknown')}")
                print(f"Turn Type: {config.get('turn_type', 'Unknown')}")
            
            print(f"Goal Achieved: {mismatch.get('goal_achieved')}")
            print(f"All Scores: {mismatch.get('all_scores', [])}")
            
            # Show conversation turns
            turns = mismatch.get('turns', [])
            if turns:
                print(f"Conversation Turns ({len(turns)}):")
                for turn in turns[:3]:  # Show first 3 turns
                    print(f"  Round {turn['round']}: score={turn['score']}")
                    print(f"    User: {turn['user']}")
                    print(f"    Assistant: {turn['assistant']}")
                if len(turns) > 3:
                    print(f"  ... and {len(turns) - 3} more turns")
            
            print("-" * 50)
        
        if len(mismatches) > 10:
            print(f"\n... and {len(mismatches) - 10} more mismatches")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    # Count by model
    model_stats = {}
    tactic_stats = {}
    
    for mismatch in mismatches:
        if mismatch.get('config'):
            model = mismatch['config'].get('target_model', 'Unknown')
            tactic = mismatch['config'].get('jailbreak_tactic', 'Unknown')
            
            model_stats[model] = model_stats.get(model, 0) + 1
            tactic_stats[tactic] = tactic_stats.get(tactic, 0) + 1
    
    if model_stats:
        print("\nMismatches by Model:")
        for model, count in sorted(model_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {model}: {count}")
    
    if tactic_stats:
        print("\nMismatches by Tactic:")
        for tactic, count in sorted(tactic_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {tactic}: {count}")

if __name__ == "__main__":
    main()