#!/usr/bin/env python3
"""
Analyze Human vs AI Meta-Evaluator Disagreements

This script compares the 77 overlapping human/meta-evaluator files one by one
to understand why the AI meta-evaluator is reaching different conclusions than
the human evaluator.
"""

import pandas as pd
import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict

def load_data() -> Tuple[pd.DataFrame, Dict]:
    """Load the human-AI comparison data and detailed analysis"""
    
    # Load the comparison CSV
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    
    # Load the detailed AI meta-evaluation analysis
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    
    # Create a lookup dict for detailed analysis by filename
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    return comparison_df, analysis_lookup

def analyze_disagreements(comparison_df: pd.DataFrame, analysis_lookup: Dict) -> Dict:
    """Analyze each disagreement case in detail"""
    
    disagreements = comparison_df[comparison_df['agreement'] == False].copy()
    
    detailed_disagreements = []
    
    for _, row in disagreements.iterrows():
        filename = row['filename']
        
        # Get detailed analysis for this file
        if filename in analysis_lookup:
            analysis = analysis_lookup[filename]
            
            # Determine the type of disagreement
            human_assessment = 'false_positive' if row['human_false_positive'] else 'true_positive'
            ai_assessment = 'found_issues' if row['ai_found_issues'] else 'no_issues'
            
            # Get AI's specific issue findings
            ai_issues = {
                'rephrasing': row['rephrasing_issues'],
                'attacker_failure': row['attacker_failure_issues'], 
                'benign_elaboration': row['benign_elaboration'],
                'capability': row['capability_issues'],
                'multi_step': row['multi_step_issues'],
                'soft_refusal': row['soft_refusal']
            }
            
            # Get AI's reasoning for each issue type
            ai_reasoning = {
                'rephrasing': analysis.get('rephrasing_issues', {}).get('reasoning', 'N/A'),
                'attacker_failure': analysis.get('attacker_failure_issues', {}).get('reasoning', 'N/A'),
                'benign_elaboration': analysis.get('benign_elaboration', {}).get('reasoning', 'N/A'),
                'capability': analysis.get('capability_issues', {}).get('reasoning', 'N/A'),
                'multi_step': analysis.get('multi_step_issues', {}).get('reasoning', 'N/A'),
                'soft_refusal': analysis.get('soft_refusal', {}).get('reasoning', 'N/A')
            }
            
            disagreement_detail = {
                'filename': filename,
                'test_case': row['test_case'],
                'jailbreak_tactic': row['jailbreak_tactic'],
                'target_model': row['target_model_x'],
                'human_assessment': human_assessment,
                'ai_assessment': ai_assessment,
                'ai_corrected_goal_achieved': analysis.get('corrected_evaluation', {}).get('goal_achieved', None),
                'ai_overall_assessment': analysis.get('overall_assessment', 'N/A'),
                'ai_issues_found': ai_issues,
                'ai_reasoning': ai_reasoning,
                'conversation_rounds': len([k for k in analysis.get('conversation_data', {}).keys() if k.startswith('round_')]),
                'original_evaluator_decision': row['decision']
            }
            
            detailed_disagreements.append(disagreement_detail)
    
    # Convert tuple keys to strings for JSON serialization
    disagreement_types = disagreements.groupby(['human_false_positive', 'ai_found_issues']).size().to_dict()
    disagreement_types_str = {str(k): v for k, v in disagreement_types.items()}
    
    return {
        'total_disagreements': len(disagreements),
        'disagreement_types': disagreement_types_str,
        'detailed_cases': detailed_disagreements
    }

def categorize_disagreement_reasons(detailed_disagreements: List[Dict]) -> Dict:
    """Categorize the main reasons for disagreements"""
    
    disagreement_patterns = defaultdict(list)
    
    for case in detailed_disagreements:
        human_fp = case['human_assessment'] == 'false_positive'
        ai_found_issues = case['ai_assessment'] == 'found_issues'
        
        # Main disagreement categories
        if human_fp and ai_found_issues:
            # Human says false positive, AI found issues
            disagreement_patterns['human_fp_ai_issues'].append(case)
        elif not human_fp and not ai_found_issues:
            # Human says true positive, AI found no issues  
            disagreement_patterns['human_tp_ai_no_issues'].append(case)
        elif human_fp and not ai_found_issues:
            # Both agree it's problematic (shouldn't happen in disagreements)
            disagreement_patterns['both_agree_problematic'].append(case)
        elif not human_fp and ai_found_issues:
            # Both think there are issues (shouldn't happen in disagreements)
            disagreement_patterns['both_agree_issues'].append(case)
    
    return disagreement_patterns

def analyze_ai_issue_patterns(detailed_disagreements: List[Dict]) -> Dict:
    """Analyze what types of issues the AI most commonly finds"""
    
    issue_frequency = defaultdict(int)
    issue_combinations = defaultdict(int)
    
    for case in detailed_disagreements:
        found_issues = []
        for issue_type, score in case['ai_issues_found'].items():
            if score > 0.5:  # High confidence threshold
                issue_frequency[issue_type] += 1
                found_issues.append(issue_type)
        
        if found_issues:
            issue_combinations[tuple(sorted(found_issues))] += 1
    
    # Convert tuple keys to strings for JSON serialization
    issue_combinations_str = {str(k): v for k, v in issue_combinations.items()}
    
    return {
        'individual_issues': dict(issue_frequency),
        'issue_combinations': issue_combinations_str
    }

def generate_case_summaries(detailed_disagreements: List[Dict]) -> List[Dict]:
    """Generate concise summaries for each disagreement case"""
    
    summaries = []
    
    for case in detailed_disagreements:
        # Identify primary AI issues (score > 0.5)
        primary_issues = [issue for issue, score in case['ai_issues_found'].items() if score > 0.5]
        
        # Create summary
        summary = {
            'filename': case['filename'],
            'test_case': case['test_case'],
            'tactic': case['jailbreak_tactic'],
            'disagreement_type': f"Human: {case['human_assessment']}, AI: {case['ai_assessment']}",
            'primary_ai_issues': primary_issues,
            'ai_overall_reasoning': case['ai_overall_assessment'][:200] + "..." if len(case['ai_overall_assessment']) > 200 else case['ai_overall_assessment'],
            'conversation_length': case['conversation_rounds']
        }
        
        summaries.append(summary)
    
    return summaries

def save_analysis_results(results: Dict, output_file: str = 'human_ai_disagreement_analysis.json'):
    """Save the complete analysis to a JSON file"""
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Detailed analysis saved to {output_file}")

def print_summary_report(results: Dict):
    """Print a summary report of the disagreement analysis"""
    
    print("=" * 80)
    print("HUMAN vs AI META-EVALUATOR DISAGREEMENT ANALYSIS")
    print("=" * 80)
    
    print(f"\nTotal files analyzed: {results['total_files']}")
    print(f"Total disagreements: {results['disagreement_analysis']['total_disagreements']}")
    print(f"Agreement rate: {(results['total_files'] - results['disagreement_analysis']['total_disagreements']) / results['total_files'] * 100:.1f}%")
    
    print("\nDisagreement breakdown:")
    patterns = results['disagreement_patterns']
    for pattern, cases in patterns.items():
        print(f"  {pattern}: {len(cases)} cases")
    
    print("\nMost common AI-identified issues in disagreements:")
    issue_freq = results['ai_issue_patterns']['individual_issues']
    for issue, count in sorted(issue_freq.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue}: {count} cases")
    
    print("\nSample disagreement cases:")
    for i, summary in enumerate(results['case_summaries'][:5], 1):
        print(f"\n{i}. {summary['filename']}")
        print(f"   Test case: {summary['test_case']} | Tactic: {summary['tactic']}")
        print(f"   {summary['disagreement_type']}")
        print(f"   AI found: {', '.join(summary['primary_ai_issues']) if summary['primary_ai_issues'] else 'No major issues'}")
        print(f"   Reasoning: {summary['ai_overall_reasoning']}")

def main():
    """Main analysis function"""
    
    print("Loading data...")
    comparison_df, analysis_lookup = load_data()
    
    print("Analyzing disagreements...")
    disagreement_analysis = analyze_disagreements(comparison_df, analysis_lookup)
    
    print("Categorizing disagreement patterns...")
    disagreement_patterns = categorize_disagreement_reasons(disagreement_analysis['detailed_cases'])
    
    print("Analyzing AI issue patterns...")
    ai_issue_patterns = analyze_ai_issue_patterns(disagreement_analysis['detailed_cases'])
    
    print("Generating case summaries...")
    case_summaries = generate_case_summaries(disagreement_analysis['detailed_cases'])
    
    # Compile results
    results = {
        'total_files': len(comparison_df),
        'disagreement_analysis': disagreement_analysis,
        'disagreement_patterns': disagreement_patterns,
        'ai_issue_patterns': ai_issue_patterns,
        'case_summaries': case_summaries
    }
    
    # Save and display results
    save_analysis_results(results)
    print_summary_report(results)
    
    return results

if __name__ == "__main__":
    main() 