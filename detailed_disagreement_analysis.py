#!/usr/bin/env python3
"""
Detailed Disagreement Analysis

This script provides in-depth analysis of specific disagreement cases between
human and AI meta-evaluators, showing conversation content and reasoning.
"""

import pandas as pd
import json
import textwrap
from typing import Dict, List

def load_analysis_results():
    """Load the disagreement analysis results"""
    with open('human_ai_disagreement_analysis.json', 'r') as f:
        return json.load(f)

def print_case_details(case: Dict, analysis_lookup: Dict):
    """Print detailed information about a disagreement case"""
    filename = case['filename']
    
    print("=" * 100)
    print(f"CASE: {filename}")
    print("=" * 100)
    
    print(f"Test Case: {case['test_case']}")
    print(f"Jailbreak Tactic: {case['jailbreak_tactic']}")
    print(f"Target Model: {case['target_model']}")
    print(f"Original Evaluator Decision: {case['original_evaluator_decision']}")
    print(f"Human Assessment: {case['human_assessment']}")
    print(f"AI Assessment: {case['ai_assessment']}")
    print(f"AI Corrected Goal Achieved: {case.get('ai_corrected_goal_achieved', 'N/A')}")
    
    # Get conversation data
    if filename in analysis_lookup:
        conv_data = analysis_lookup[filename].get('conversation_data', {})
        
        print(f"\nOriginal Harmful Goal: {conv_data.get('task', 'N/A')}")
        
        # Print conversation rounds
        print("\n" + "-" * 50)
        print("CONVERSATION ROUNDS:")
        print("-" * 50)
        
        round_count = 0
        for key in sorted(conv_data.keys()):
            if key.startswith('round_'):
                round_count += 1
                round_data = conv_data[key]
                
                print(f"\nROUND {round_count}:")
                print(f"Attacker Prompt: {textwrap.fill(round_data.get('tactic_prompt', 'N/A'), width=80)}")
                print(f"Target Response: {textwrap.fill(round_data.get('target_response', 'N/A'), width=80)}")
                print(f"Round Score: {round_data.get('score', 'N/A')}")
                
                if 'summary' in round_data:
                    print(f"Evaluator Summary: {textwrap.fill(round_data['summary'], width=80)}")
        
        print(f"\nFinal Goal Achieved: {conv_data.get('goal_achieved', 'N/A')}")
    
    # AI's issue analysis
    print("\n" + "-" * 50)
    print("AI META-EVALUATOR ISSUE ANALYSIS:")
    print("-" * 50)
    
    high_confidence_issues = []
    for issue_type, score in case['ai_issues_found'].items():
        if score > 0.5:
            high_confidence_issues.append(issue_type)
            print(f"\n{issue_type.upper()} (Score: {score}):")
            reasoning = case['ai_reasoning'].get(issue_type, 'N/A')
            print(textwrap.fill(reasoning, width=80, initial_indent='  ', subsequent_indent='  '))
    
    if not high_confidence_issues:
        print("No high-confidence issues found by AI.")
    
    print(f"\nAI Overall Assessment:")
    print(textwrap.fill(case['ai_overall_assessment'], width=80, initial_indent='  ', subsequent_indent='  '))
    
    print("\n" + "=" * 100)

def analyze_disagreement_patterns(results: Dict):
    """Analyze patterns in the disagreements"""
    
    print("\n" + "=" * 100)
    print("DISAGREEMENT PATTERN ANALYSIS")
    print("=" * 100)
    
    # Load original data for cross-reference
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    # Analyze each disagreement type
    patterns = results['disagreement_patterns']
    
    print(f"\nTotal disagreements: {results['disagreement_analysis']['total_disagreements']}")
    
    for pattern_name, cases in patterns.items():
        print(f"\n{pattern_name.upper()}: {len(cases)} cases")
        print("-" * 50)
        
        if pattern_name == 'both_agree_issues':
            print("These are cases where humans marked as 'true positive' but AI found evaluation issues")
            print("This suggests the AI is identifying problems with the evaluation that humans missed")
        
        elif pattern_name == 'human_fp_ai_issues':
            print("These are cases where humans marked as 'false positive' but AI found issues with the evaluation")
            print("This suggests humans correctly identified evaluation problems, but AI also found additional issues")
        
        elif pattern_name == 'human_tp_ai_no_issues':
            print("These are cases where humans marked as 'true positive' but AI found no evaluation issues")
            print("This suggests AI thinks the evaluation was correct, but humans thought it was wrong")
        
        # Show a few examples
        print(f"\nExample cases (showing first 3):")
        for i, case in enumerate(cases[:3]):
            print(f"\n{i+1}. {case['filename']}")
            print(f"   Test: {case['test_case']} | Tactic: {case['jailbreak_tactic']}")
            print(f"   Primary AI issues: {case.get('primary_issues', [])}")

def main():
    """Main analysis function"""
    
    # Load analysis results
    results = load_analysis_results()
    
    # Load original data for cross-reference
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    print("DETAILED HUMAN vs AI META-EVALUATOR DISAGREEMENT ANALYSIS")
    print("=" * 100)
    
    # Analyze disagreement patterns first
    analyze_disagreement_patterns(results)
    
    print(f"\n\nDetailed case analysis will show {len(results['case_summaries'])} disagreement cases...")
    print("Press Enter to continue or 'q' to quit:")
    response = input()
    
    if response.lower() == 'q':
        return
    
    # Show detailed cases
    detailed_cases = results['disagreement_analysis']['detailed_cases']
    
    # Group by pattern for better organization
    patterns = results['disagreement_patterns']
    
    for pattern_name, pattern_cases in patterns.items():
        print(f"\n\n{'='*100}")
        print(f"DETAILED ANALYSIS: {pattern_name.upper()}")
        print(f"{'='*100}")
        
        for i, case in enumerate(pattern_cases[:5]):  # Show first 5 of each type
            print_case_details(case, analysis_lookup)
            
            if i < len(pattern_cases) - 1:
                print("\nPress Enter for next case, 's' to skip to next pattern, or 'q' to quit:")
                response = input()
                if response.lower() == 'q':
                    return
                elif response.lower() == 's':
                    break

if __name__ == "__main__":
    main() 