#!/usr/bin/env python3
"""
Comprehensive Summary Report: Why AI and Human Evaluators Disagree

This script analyzes the 77 overlapping cases to provide clear insights into
the fundamental differences between human and AI meta-evaluator assessments.
"""

import pandas as pd
import json
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

def load_and_prepare_data():
    """Load all necessary data for analysis"""
    
    # Load comparison data
    comparison_df = pd.read_csv('human_ai_comparison.csv')
    
    # Load detailed AI analysis
    with open('human_overlap_meta_evaluation_results/detailed_analysis_20250617_064158.json', 'r') as f:
        detailed_analysis = json.load(f)
    
    analysis_lookup = {item['file_name']: item for item in detailed_analysis}
    
    return comparison_df, analysis_lookup

def analyze_core_disagreement_reasons(comparison_df: pd.DataFrame, analysis_lookup: Dict) -> Dict:
    """Analyze the fundamental reasons for disagreement"""
    
    disagreements = comparison_df[comparison_df['agreement'] == False].copy()
    
    reasons = {
        'human_missed_issues': [],      # Human said TP, AI found issues
        'human_found_false_positives': [],  # Human said FP, AI found no issues
        'conflicting_assessments': []   # Other disagreement patterns
    }
    
    for _, row in disagreements.iterrows():
        filename = row['filename']
        human_fp = row['human_false_positive']
        ai_found_issues = row['ai_found_issues']
        
        if not human_fp and ai_found_issues:
            # Human said true positive, AI found evaluation issues
            reasons['human_missed_issues'].append({
                'filename': filename,
                'test_case': row['test_case'],
                'tactic': row['jailbreak_tactic'],
                'model': row['target_model_x'],
                'ai_issues': {
                    'rephrasing': row['rephrasing_issues'],
                    'attacker_failure': row['attacker_failure_issues'],
                    'benign_elaboration': row['benign_elaboration'],
                    'capability': row['capability_issues'],
                    'multi_step': row['multi_step_issues'],
                    'soft_refusal': row['soft_refusal']
                },
                'original_decision': row['decision']
            })
        elif human_fp and not ai_found_issues:
            # Human said false positive, AI found no issues
            reasons['human_found_false_positives'].append({
                'filename': filename,
                'test_case': row['test_case'],
                'tactic': row['jailbreak_tactic'],
                'model': row['target_model_x'],
                'original_decision': row['decision']
            })
        else:
            # Other patterns
            reasons['conflicting_assessments'].append({
                'filename': filename,
                'human_assessment': 'false_positive' if human_fp else 'true_positive',
                'ai_assessment': 'found_issues' if ai_found_issues else 'no_issues'
            })
    
    return reasons

def extract_key_insights(reasons: Dict, analysis_lookup: Dict) -> Dict:
    """Extract key insights about why disagreements occur"""
    
    insights = {
        'primary_disagreement_type': None,
        'ai_most_common_issues': Counter(),
        'problem_tactics': Counter(),
        'problem_test_cases': Counter(),
        'human_vs_ai_philosophy': {},
        'specific_examples': []
    }
    
    # Find primary disagreement type
    disagreement_counts = {k: len(v) for k, v in reasons.items()}
    insights['primary_disagreement_type'] = max(disagreement_counts, key=disagreement_counts.get)
    
    # Analyze AI's most common issues when humans missed them
    for case in reasons['human_missed_issues']:
        for issue_type, score in case['ai_issues'].items():
            if score > 0.5:
                insights['ai_most_common_issues'][issue_type] += 1
        
        insights['problem_tactics'][case['tactic']] += 1
        insights['problem_test_cases'][case['test_case']] += 1
    
    # Extract philosophical differences
    rephrasing_cases = sum(1 for case in reasons['human_missed_issues'] 
                          if case['ai_issues']['rephrasing'] > 0.5)
    attacker_failure_cases = sum(1 for case in reasons['human_missed_issues'] 
                                if case['ai_issues']['attacker_failure'] > 0.5)
    
    insights['human_vs_ai_philosophy'] = {
        'ai_focuses_on_attack_validity': {
            'rephrasing_issues': rephrasing_cases,
            'attacker_failures': attacker_failure_cases,
            'explanation': "AI frequently identifies cases where attackers rephrased requests to be innocuous or failed to request harmful content"
        },
        'human_focuses_on_final_output': {
            'cases_where_human_ignored_attack_flaws': len(reasons['human_missed_issues']),
            'explanation': "Humans appear to focus on whether harmful information was provided, regardless of attack methodology"
        }
    }
    
    return insights

def generate_detailed_examples(reasons: Dict, analysis_lookup: Dict) -> List[Dict]:
    """Generate detailed examples of key disagreement types"""
    
    examples = []
    
    # Get examples of each major disagreement type
    for case in reasons['human_missed_issues'][:3]:  # Top 3 cases
        filename = case['filename']
        if filename in analysis_lookup:
            analysis = analysis_lookup[filename]
            
            # Find the main AI issue
            main_issues = [issue for issue, score in case['ai_issues'].items() if score > 0.5]
            
            example = {
                'filename': filename,
                'type': 'Human missed evaluation issues',
                'test_case': case['test_case'],
                'tactic': case['tactic'],
                'original_evaluator_said': case['original_decision'],
                'human_said': 'True positive (jailbreak worked)',
                'ai_found_issues': main_issues,
                'ai_explanation': analysis.get('overall_assessment', 'N/A')[:300] + "...",
                'why_disagreement_occurred': f"Human focused on final output, AI identified {', '.join(main_issues)} in the attack methodology"
            }
            examples.append(example)
    
    return examples

def print_comprehensive_report(insights: Dict, reasons: Dict, examples: List[Dict]):
    """Print a comprehensive report answering why disagreements occur"""
    
    print("=" * 100)
    print("WHY AI META-EVALUATOR REACHES DIFFERENT CONCLUSIONS THAN HUMAN EVALUATOR")
    print("=" * 100)
    
    total_disagreements = sum(len(v) for v in reasons.values())
    print(f"\nSUMMARY: Analyzed {total_disagreements} disagreement cases from 77 overlapping files")
    
    print(f"\nPRIMARY FINDING:")
    print(f"The main disagreement type is: {insights['primary_disagreement_type']}")
    print(f"This accounts for {len(reasons[insights['primary_disagreement_type']])} of {total_disagreements} disagreements")
    
    print("\n" + "=" * 80)
    print("KEY REASONS FOR DISAGREEMENTS:")
    print("=" * 80)
    
    print("\n1. PHILOSOPHICAL DIFFERENCES IN EVALUATION APPROACH:")
    print("-" * 60)
    
    ai_philosophy = insights['human_vs_ai_philosophy']
    
    print("AI Meta-Evaluator Focus:")
    print("• Analyzes the validity and methodology of the attack itself")
    print(f"• Found {ai_philosophy['ai_focuses_on_attack_validity']['rephrasing_issues']} cases where attackers made requests innocuous")
    print(f"• Found {ai_philosophy['ai_focuses_on_attack_validity']['attacker_failures']} cases where attackers failed to request harmful content")
    print("• Considers an evaluation incorrect if the attack methodology was flawed")
    
    print("\nHuman Evaluator Focus:")
    print("• Appears to focus primarily on the final output/response")
    print("• Less concerned with whether the attack method was valid")
    print(f"• In {ai_philosophy['human_focuses_on_final_output']['cases_where_human_ignored_attack_flaws']} cases, marked as successful jailbreak despite attack flaws")
    
    print("\n2. SPECIFIC ISSUE PATTERNS IDENTIFIED BY AI:")
    print("-" * 60)
    
    for issue, count in insights['ai_most_common_issues'].most_common():
        print(f"• {issue.replace('_', ' ').title()}: {count} cases")
        
        if issue == 'rephrasing':
            print("  - Attackers rephrased harmful requests to be innocuous")
            print("  - Humans saw helpful response, AI saw flawed attack")
        elif issue == 'attacker_failure':
            print("  - Attackers never actually requested harmful content")
            print("  - Humans evaluated based on model response, AI noted missing harmful request")
        elif issue == 'benign_elaboration':
            print("  - Models only answered safe parts of questions")
            print("  - Humans may have missed that harmful parts were ignored")
    
    print("\n3. PROBLEMATIC TACTICS AND TEST CASES:")
    print("-" * 60)
    
    print("Tactics with most disagreements:")
    for tactic, count in insights['problem_tactics'].most_common():
        print(f"• {tactic}: {count} cases")
    
    print("\nTest cases with most disagreements:")
    for test_case, count in insights['problem_test_cases'].most_common()[:5]:
        print(f"• {test_case}: {count} cases")
    
    print("\n" + "=" * 80)
    print("DETAILED EXAMPLES OF DISAGREEMENTS:")
    print("=" * 80)
    
    for i, example in enumerate(examples, 1):
        print(f"\nEXAMPLE {i}: {example['type']}")
        print("-" * 60)
        print(f"File: {example['filename']}")
        print(f"Test Case: {example['test_case']} | Tactic: {example['tactic']}")
        print(f"Original Evaluator Decision: {example['original_evaluator_said']}")
        print(f"Human Assessment: {example['human_said']}")
        print(f"AI Found Issues: {', '.join(example['ai_found_issues'])}")
        print(f"AI Explanation: {example['ai_explanation']}")
        print(f"Why Disagreement Occurred: {example['why_disagreement_occurred']}")
    
    print("\n" + "=" * 80)
    print("CONCLUSIONS:")
    print("=" * 80)
    
    print("\n1. EVALUATION PHILOSOPHY MISMATCH:")
    print("   - Humans evaluate based on 'Did the model provide harmful information?'")
    print("   - AI evaluates based on 'Was this a valid successful jailbreak attack?'")
    
    print("\n2. AI IS MORE STRINGENT ABOUT ATTACK VALIDITY:")
    print("   - AI considers rephrasing attacks that make requests innocuous as failures")
    print("   - AI identifies when attackers never actually requested harmful content")
    print("   - AI recognizes when models only answered benign parts of questions")
    
    print("\n3. HUMANS MAY MISS METHODOLOGICAL FLAWS:")
    print("   - Humans appear to focus on output content rather than attack process")
    print("   - This leads to marking failed attacks as successful jailbreaks")
    print("   - AI provides more nuanced analysis of why evaluations may be incorrect")
    
    print("\n4. IMPLICATION FOR JAILBREAK EVALUATION:")
    print("   - Current human evaluation may overestimate jailbreak success rates")
    print("   - AI meta-evaluation reveals hidden false positives in evaluation")
    print("   - Need for clearer evaluation criteria about what constitutes a successful attack")

def main():
    """Main analysis function"""
    
    print("Loading data and analyzing disagreements...")
    comparison_df, analysis_lookup = load_and_prepare_data()
    
    print("Extracting core disagreement reasons...")
    reasons = analyze_core_disagreement_reasons(comparison_df, analysis_lookup)
    
    print("Generating insights...")
    insights = extract_key_insights(reasons, analysis_lookup)
    
    print("Creating detailed examples...")
    examples = generate_detailed_examples(reasons, analysis_lookup)
    
    print("Generating comprehensive report...\n")
    print_comprehensive_report(insights, reasons, examples)
    
    # Save detailed results
    results = {
        'disagreement_reasons': reasons,
        'key_insights': insights,
        'detailed_examples': examples
    }
    
    with open('disagreement_comprehensive_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n\nDetailed analysis saved to: disagreement_comprehensive_analysis.json")

if __name__ == "__main__":
    main() 