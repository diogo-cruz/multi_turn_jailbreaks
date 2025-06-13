#!/usr/bin/env python3
"""
Detailed analysis of edge cases where goal_achieved: false but contains rounds with score: 1.0
"""
import json
from pathlib import Path

def analyze_edge_case_file(file_path):
    """Analyze a single edge case file in detail"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse all lines
    config = {}
    rounds = []
    goal_achieved = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        data = json.loads(line)
        
        if 'target_model' in data:
            config = data
        elif 'round' in data:
            rounds.append(data)
        elif 'goal_achieved' in data:
            goal_achieved = data.get('goal_achieved')
    
    return config, rounds, goal_achieved

def analyze_conversation_flow(rounds):
    """Analyze the conversation flow to understand what happens after score=1.0"""
    scores = []
    score_1_rounds = []
    
    for i, round_data in enumerate(rounds):
        score = round_data.get('score', 'N/A')
        scores.append(score)
        if score == 1.0:
            score_1_rounds.append(i)
    
    analysis = {
        'total_rounds': len(rounds),
        'all_scores': scores,
        'score_1_rounds': score_1_rounds,
        'min_score': min([s for s in scores if isinstance(s, (int, float))]),
        'max_score': max([s for s in scores if isinstance(s, (int, float))]),
        'avg_score': sum([s for s in scores if isinstance(s, (int, float))]) / len([s for s in scores if isinstance(s, (int, float))])
    }
    
    # Analyze what happens after each score=1.0
    post_score_1_analysis = []
    for round_idx in score_1_rounds:
        subsequent_rounds = rounds[round_idx+1:] if round_idx+1 < len(rounds) else []
        subsequent_scores = [r.get('score') for r in subsequent_rounds]
        
        post_score_1_analysis.append({
            'score_1_round': round_idx,
            'subsequent_rounds': len(subsequent_rounds),
            'subsequent_scores': subsequent_scores,
            'recovery_rounds': len([s for s in subsequent_scores if s == 10])
        })
    
    analysis['post_score_1_analysis'] = post_score_1_analysis
    return analysis

def print_conversation_snippet(rounds, round_idx, context=1):
    """Print a snippet of conversation around a specific round"""
    start = max(0, round_idx - context)
    end = min(len(rounds), round_idx + context + 1)
    
    for i in range(start, end):
        round_data = rounds[i]
        score = round_data.get('score', 'N/A')
        user_msg = round_data.get('user', '')[:100] + '...' if len(round_data.get('user', '')) > 100 else round_data.get('user', '')
        assistant_msg = round_data.get('assistant', '')[:200] + '...' if len(round_data.get('assistant', '')) > 200 else round_data.get('assistant', '')
        
        marker = " *** SCORE 1.0 ***" if score == 1.0 else ""
        print(f"  Round {i+1} (Score: {score}){marker}")
        print(f"    User: {user_msg}")
        print(f"    Assistant: {assistant_msg}")
        print()

def main():
    # Load edge cases from previous analysis
    with open('edge_cases_analysis.json', 'r') as f:
        edge_cases = json.load(f)
    
    print(f"Analyzing {len(edge_cases)} edge cases in detail...")
    print("=" * 80)
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\nEDGE CASE {i}: {Path(case['file']).name}")
        print(f"Model: {case['model_name']}")
        print(f"Tactic: {case['tactic']}")
        print(f"Harm Category: {case['harm_category']}")
        print(f"Goal Achieved: {case['goal_achieved']}")
        print(f"Total Rounds: {case['num_rounds']}")
        print(f"Rounds with Score 1.0: {case['rounds_with_score_1']}")
        print("-" * 60)
        
        # Analyze the actual file content
        config, rounds, goal_achieved = analyze_edge_case_file(case['file'])
        analysis = analyze_conversation_flow(rounds)
        
        print(f"Score Analysis:")
        print(f"  All scores: {analysis['all_scores']}")
        print(f"  Min/Max/Avg: {analysis['min_score']:.1f}/{analysis['max_score']:.1f}/{analysis['avg_score']:.1f}")
        print()
        
        # Show what happens after each score=1.0 round
        for post_analysis in analysis['post_score_1_analysis']:
            score_1_round = post_analysis['score_1_round']
            print(f"After Score 1.0 in Round {score_1_round + 1}:")
            print(f"  - {post_analysis['subsequent_rounds']} subsequent rounds")
            print(f"  - Subsequent scores: {post_analysis['subsequent_scores']}")
            print(f"  - Recovery rounds (score 10): {post_analysis['recovery_rounds']}")
            print()
            
            # Show conversation snippet around the score=1.0 round
            print(f"Conversation around Round {score_1_round + 1}:")
            print_conversation_snippet(rounds, score_1_round, context=2)
        
        print("=" * 80)

if __name__ == "__main__":
    main()