#!/usr/bin/env python3
"""
Test the corrected refusal handling function.
"""

from asr_analysis_utils import get_max_score_by_round_with_refusals, read_json_file

def test_refusal_function():
    """Test the corrected refusal handling."""
    file_path = "clean_results/final_runs/batch6B/direct_request/direct_request_terrorist_recruitment_claude-3.5-sonnet_multi_turn_sample1_2025_06_27_02_14_17.jsonl"
    
    print(f"Testing with: {file_path}")
    
    data = read_json_file(file_path)
    result = get_max_score_by_round_with_refusals(data, 8)
    
    print(f"Function returned {len(result)} rounds:")
    
    # Show all rounds
    max_round = max([int(k.replace('max_score_by_', '').replace('_rounds', '')) for k in result.keys()])
    
    for r in range(1, min(20, max_round + 1)):  # Show first 20 rounds or all if fewer
        key = f'max_score_by_{r}_rounds'
        if key in result:
            print(f"  Round {r}: max score = {result[key]}")
    
    print(f"\nTotal rounds with data: {max_round}")
    print(f"Expected: 8 regular rounds + 8 refusals = 16 total rounds")
    
    if max_round >= 16:
        print("✅ SUCCESS: Function correctly extends beyond 8 rounds due to refusals")
    else:
        print("❌ FAILURE: Function did not extend to expected 16 rounds")
    
    # Check if scores make sense
    if result.get('max_score_by_5_rounds', 0) > 0:
        print("✅ SUCCESS: Found non-zero score at round 5 (matches debug data)")
    else:
        print("❌ FAILURE: Expected non-zero score at round 5")

if __name__ == "__main__":
    test_refusal_function()