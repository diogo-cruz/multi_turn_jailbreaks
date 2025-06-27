#!/usr/bin/env python3
"""
Debug script to understand refusal handling in multi-turn data.
"""

import json
from asr_analysis_utils import read_json_file

def analyze_jsonl_structure(file_path):
    """Analyze the structure of a JSONL file to understand refusals."""
    print(f"Analyzing: {file_path}")
    
    data = read_json_file(file_path)
    
    # Parse data
    entries = []
    for line in data.strip().split('\n'):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    print(f"Total entries: {len(entries)}")
    
    # Categorize entries
    metadata_entries = []
    refused_entries = []
    numeric_score_entries = []
    goal_achieved_entries = []
    other_entries = []
    
    for entry in entries:
        if 'target_base_url' in entry or 'model_base_url' in entry:
            metadata_entries.append(entry)
        elif 'goal_achieved' in entry:
            goal_achieved_entries.append(entry)
        elif 'score' in entry:
            score = entry.get('score')
            if score == "refused":
                refused_entries.append(entry)
            elif isinstance(score, (int, float)):
                numeric_score_entries.append(entry)
            else:
                other_entries.append(entry)
        else:
            other_entries.append(entry)
    
    print(f"Metadata entries: {len(metadata_entries)}")
    print(f"Refused entries: {len(refused_entries)}")
    print(f"Numeric score entries: {len(numeric_score_entries)}")
    print(f"Goal achieved entries: {len(goal_achieved_entries)}")
    print(f"Other entries: {len(other_entries)}")
    
    print("\nRefused entries by round:")
    for entry in refused_entries[:5]:  # Show first 5
        round_num = entry.get('round', 'unknown')
        print(f"  Round {round_num}: score = '{entry.get('score')}'")
    
    print("\nNumeric score entries by round:")
    for entry in numeric_score_entries[:5]:  # Show first 5
        round_num = entry.get('round', 'unknown')
        print(f"  Round {round_num}: score = {entry.get('score')}")
    
    # Show how the original function would process this
    print(f"\nOriginal processing would give:")
    round_scores = {}
    for entry in numeric_score_entries:
        # For multi-turn, we need to extract scores from evaluation entries after each round
        if 'goal' in entry:  # This seems to be the evaluation entries
            round_num = len(round_scores) + 1
            round_scores[round_num] = entry.get('score', 0.0)
    
    print(f"Regular round scores: {round_scores}")
    print(f"Total refusals: {len(refused_entries)}")
    print(f"With refusals, should have {len(round_scores) + len(refused_entries)} total rounds")
    
    return len(round_scores), len(refused_entries)

def main():
    # Test with the file we know has refusals
    file_path = "clean_results/final_runs/batch6B/direct_request/direct_request_terrorist_recruitment_claude-3.5-sonnet_multi_turn_sample1_2025_06_27_02_14_17.jsonl"
    
    regular_rounds, refusal_count = analyze_jsonl_structure(file_path)
    
    print(f"\n=== EXPECTED BEHAVIOR ===")
    print(f"Regular rounds: {regular_rounds}")
    print(f"Refusal count: {refusal_count}")
    print(f"Total rounds (with refusals): {regular_rounds + refusal_count}")
    print(f"Max score by round should extend to round {regular_rounds + refusal_count}")

if __name__ == "__main__":
    main()