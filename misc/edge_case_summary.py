#!/usr/bin/env python3
"""
Summary analysis of edge cases
"""
import json
from pathlib import Path

def main():
    # Load edge cases from previous analysis
    with open('edge_cases_analysis.json', 'r') as f:
        edge_cases = json.load(f)
    
    print("EDGE CASE ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Total edge cases found: {len(edge_cases)}")
    print()
    
    # Model distribution
    models = [case['model_name'] for case in edge_cases]
    model_counts = {}
    for model in models:
        model_counts[model] = model_counts.get(model, 0) + 1
    
    print("Models involved:")
    for model, count in model_counts.items():
        print(f"  - {model}: {count} case(s)")
    print()
    
    # Tactic distribution
    tactics = [case['tactic'] for case in edge_cases]
    tactic_counts = {}
    for tactic in tactics:
        tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
    
    print("Tactics involved:")
    for tactic, count in tactic_counts.items():
        print(f"  - {tactic}: {count} case(s)")
    print()
    
    # Harm categories
    harm_cats = [case['harm_category'] for case in edge_cases]
    harm_counts = {}
    for harm in harm_cats:
        harm_counts[harm] = harm_counts.get(harm, 0) + 1
    
    print("Harm categories:")
    for harm, count in harm_counts.items():
        print(f"  - {harm}: {count} case(s)")
    print()
    
    # Round analysis
    print("Round analysis:")
    total_rounds = [case['num_rounds'] for case in edge_cases]
    rounds_with_score_1 = [len(case['rounds_with_score_1']) for case in edge_cases]
    
    print(f"  Average total rounds: {sum(total_rounds) / len(total_rounds):.1f}")
    print(f"  Range of total rounds: {min(total_rounds)} - {max(total_rounds)}")
    print(f"  Average rounds with score 1.0: {sum(rounds_with_score_1) / len(rounds_with_score_1):.1f}")
    print(f"  Range of rounds with score 1.0: {min(rounds_with_score_1)} - {max(rounds_with_score_1)}")
    print()
    
    print("KEY FINDINGS:")
    print("-" * 30)
    print()
    print("1. PATTERN ANALYSIS:")
    print("   - All edge cases involve the 'actor_attack' tactic")
    print("   - Most involve smaller Llama models (3.2-1b, 3.2-3b), but also some larger models")
    print("   - Conversations can be quite long (8-21 rounds)")
    print()
    
    print("2. WHAT HAPPENS AFTER SCORE 1.0:")
    print("   - In most cases, the model RECOVERS after giving a score=1.0 response")
    print("   - Subsequent rounds typically return to score=10 (safe responses)")
    print("   - This suggests the model realizes it made a mistake and corrects course")
    print()
    
    print("3. WHY GOAL_ACHIEVED = FALSE:")
    print("   - Even though some rounds achieved score=1.0, the model recovered")
    print("   - The conversation doesn't end with sustained harmful outputs")
    print("   - The final state shows the model refusing to provide harmful information")
    print("   - This suggests a difference between 'momentary jailbreak' vs 'sustained jailbreak'")
    print()
    
    print("4. CONVERSATION FLOW PATTERN:")
    print("   - Attacker uses gradual escalation and social engineering")
    print("   - Model occasionally slips and provides harmful information (score=1.0)")
    print("   - Model then recognizes the request as harmful and refuses (score=10)")
    print("   - Attacker tries to capitalize on the slip but model maintains refusal")
    print()
    
    print("5. EVALUATION METHODOLOGY INSIGHT:")
    print("   - 'goal_achieved' appears to require SUSTAINED harmful output")
    print("   - A single round with score=1.0 is not sufficient")
    print("   - The evaluation considers the overall conversation outcome")
    print("   - This is actually a more robust evaluation than just checking for any score=1.0")
    print()
    
    print("6. IMPLICATIONS:")
    print("   - These are not evaluation errors - they represent nuanced cases")
    print("   - Shows that models can sometimes be briefly tricked but often recover")
    print("   - Actor attack is effective at getting momentary slips")
    print("   - The evaluation system correctly distinguishes between temporary and sustained jailbreaks")

if __name__ == "__main__":
    main()