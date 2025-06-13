#!/usr/bin/env python3
"""
Find edge cases where files have goal_achieved: false despite containing rounds with score: 1.0
"""
import json
import os
from pathlib import Path

def find_edge_cases():
    """Find files with goal_achieved: false but containing rounds with score: 1.0"""
    results_dir = Path("results")
    edge_cases = []
    
    for file_path in results_dir.glob("*.jsonl"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                continue
                
            # Parse all lines to find config, rounds, and goal_achieved
            config = {}
            rounds = []
            goal_achieved = None
            model_name = "unknown"
            tactic = "unknown"
            harm_category = "unknown"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                data = json.loads(line)
                
                # First line typically has config info
                if 'target_model' in data:
                    config = data
                    model_name = data.get('target_model', 'unknown')
                    tactic = data.get('jailbreak_tactic', 'unknown')
                    harm_category = data.get('test_case', 'unknown')
                
                # Lines with round info
                if 'round' in data:
                    rounds.append(data)
                
                # Line with goal_achieved
                if 'goal_achieved' in data:
                    goal_achieved = data.get('goal_achieved')
            
            # Check if goal_achieved is false
            if goal_achieved is not False:  # Skip if goal_achieved is True or None
                continue
                
            # Check if any round has score 1.0
            has_score_1 = False
            rounds_with_score_1 = []
            for i, round_data in enumerate(rounds):
                if round_data.get('score') == 1.0:
                    has_score_1 = True
                    rounds_with_score_1.append(i)
            
            if has_score_1:
                edge_cases.append({
                    'file': str(file_path),
                    'model_name': model_name,
                    'tactic': tactic,
                    'harm_category': harm_category,
                    'goal_achieved': goal_achieved,
                    'num_rounds': len(rounds),
                    'rounds_with_score_1': rounds_with_score_1,
                    'all_scores': [r.get('score') for r in rounds]
                })
                
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return edge_cases

def main():
    edge_cases = find_edge_cases()
    print(f"Found {len(edge_cases)} edge cases:")
    print()
    
    for i, case in enumerate(edge_cases, 1):
        print(f"{i}. {case['file']}")
        print(f"   Model: {case['model_name']}")
        print(f"   Tactic: {case['tactic']}")
        print(f"   Harm Category: {case['harm_category']}")
        print(f"   Goal Achieved: {case['goal_achieved']}")
        print(f"   Total Rounds: {case['num_rounds']}")
        print(f"   Rounds with Score 1.0: {case['rounds_with_score_1']}")
        print()
    
    # Save results for further analysis
    with open('edge_cases_analysis.json', 'w') as f:
        json.dump(edge_cases, f, indent=2)
    
    print(f"Results saved to edge_cases_analysis.json")

if __name__ == "__main__":
    main()