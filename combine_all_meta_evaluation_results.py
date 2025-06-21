#!/usr/bin/env python3
"""
Combine all AI meta-evaluation results (old 77 + new 197) and create comprehensive comparison plots.
"""

import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def load_all_human_evaluations():
    """Load all human evaluations from the JSONL file."""
    human_evaluations = []
    with open('clean_results/false_positive_annotations.jsonl', 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            human_evaluations.append({
                'filename': data['filename'],
                'decision': data['decision'],
                'test_case': data.get('test_case', ''),
                'jailbreak_tactic': data.get('jailbreak_tactic', ''),
                'target_model': data.get('target_model', ''),
                'evaluator': data.get('evaluator', ''),
                'note': data.get('note', '')
            })
    return pd.DataFrame(human_evaluations)

def load_all_updated_ai_results():
    """Load and combine all updated AI meta-evaluation results."""
    
    # 1. Load original 77 cases results
    original_77_results = {}
    df_77 = pd.read_csv('complete_77_cases_comparison.csv')
    for _, row in df_77.iterrows():
        filename = row['filename']
        goal_achieved = row['updated_ai_goal_achieved']
        original_77_results[filename] = goal_achieved
    
    print(f"Loaded {len(original_77_results)} results from original 77 cases")
    
    # 2. Load new cases results
    new_results = {}
    results_dir = 'new_cases_meta_evaluation_results'
    if os.path.exists(results_dir):
        # Find the latest results file
        for filename in os.listdir(results_dir):
            if filename.startswith('new_cases_analysis_') and filename.endswith('.json'):
                file_path = os.path.join(results_dir, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for result in data:
                        filename = result['file_name']
                        goal_achieved = result.get('corrected_evaluation', {}).get('goal_achieved', False)
                        new_results[filename] = goal_achieved
                break
    
    print(f"Loaded {len(new_results)} results from new cases")
    
    # 3. Combine all results
    all_updated_results = {**original_77_results, **new_results}
    print(f"Total updated AI results: {len(all_updated_results)}")
    
    return all_updated_results

def create_comprehensive_comparison():
    """Create comprehensive comparison plots for all available data."""
    
    # Load all human evaluations (303 total)
    human_df = load_all_human_evaluations()
    print(f"Total human evaluations: {len(human_df)}")
    
    # Load all updated AI results
    updated_ai_results = load_all_updated_ai_results()
    
    # Find overlap between human and AI evaluations
    overlap_files = set(human_df['filename']) & set(updated_ai_results.keys())
    print(f"Overlapping files (human + updated AI): {len(overlap_files)}")
    
    # Create analysis dataframe for overlapping cases
    overlap_df = human_df[human_df['filename'].isin(overlap_files)].copy()
    overlap_df['updated_ai_goal_achieved'] = overlap_df['filename'].map(updated_ai_results)
    overlap_df['updated_ai_found_issues'] = ~overlap_df['updated_ai_goal_achieved']
    overlap_df['human_false_positive'] = overlap_df['decision'] == 'false_positive'
    
    # Load original AI results for comparison (from the 77-case analysis)
    original_ai_df = pd.read_csv('human_ai_comparison_excluding_rephrasing.csv')
    
    # Calculate agreement rates for different datasets
    print("\\n" + "="*80)
    print("COMPREHENSIVE COMPARISON ANALYSIS")
    print("="*80)
    
    # 1. Agreement on overlapping cases
    updated_agreement = (overlap_df['human_false_positive'] == overlap_df['updated_ai_found_issues']).mean()
    print(f"\\nOverlapping cases ({len(overlap_df)} files):")
    print(f"  Human-Updated AI agreement: {updated_agreement:.1%}")
    
    # 2. Original 77 cases comparison (if available)
    original_77_files = set(overlap_df['filename']) & set(original_ai_df['filename']) if len(original_ai_df) > 0 else set()
    
    if len(original_77_files) > 0:
        original_subset = original_ai_df[original_ai_df['filename'].isin(original_77_files)]
        
        original_ai_found_issues = original_subset['rephrasing_issues'] > 0.5
        for col in ['attacker_failure_issues', 'benign_elaboration', 'capability_issues', 'multi_step_issues', 'soft_refusal']:
            original_ai_found_issues |= (original_subset[col] > 0.5)
        
        original_agreement = (original_subset['human_false_positive'] == original_ai_found_issues).mean()
        updated_agreement_77 = original_subset['updated_ai_agreement'].mean()
        
        print(f"\\nOriginal 77 cases subset ({len(original_subset)} files):")
        print(f"  Human-Original AI agreement: {original_agreement:.1%}")
        print(f"  Human-Updated AI agreement: {updated_agreement_77:.1%}")
        print(f"  Improvement: +{(updated_agreement_77 - original_agreement)*100:.1f} percentage points")
    
    # Create comprehensive plots
    fig, axes = plt.subplots(2, 3, figsize=(20, 13))
    fig.suptitle(f'Complete Human vs AI Meta-Evaluator Analysis ({len(overlap_df)} Total Cases)', fontsize=18, fontweight='bold')
    
    # 1. Agreement rates by dataset
    ax1 = axes[0, 0]
    
    if len(original_77_files) > 0:
        datasets = ['Original 77\\n(Original AI)', 'Original 77\\n(Updated AI)', f'All {len(overlap_df)}\\n(Updated AI)']
        agreement_rates = [original_agreement, updated_agreement_77, updated_agreement]
    else:
        datasets = [f'All {len(overlap_df)}\\n(Updated AI)']
        agreement_rates = [updated_agreement]
    
    colors = ['#ff7f7f', '#66b3ff', '#90EE90'][:len(datasets)]
    bars = ax1.bar(datasets, agreement_rates, color=colors, alpha=0.8, edgecolor='black', width=0.6)
    ax1.set_ylabel('Agreement Rate with Humans', fontsize=12)
    ax1.set_ylim(0, 1)
    ax1.set_title('Agreement Rates Across Datasets', fontsize=14, fontweight='bold')
    
    # Add percentage labels
    for bar, rate in zip(bars, agreement_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{rate:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # 2. Decision distribution in all cases
    ax2 = axes[0, 1]
    decision_counts = overlap_df['decision'].value_counts()
    wedges, texts, autotexts = ax2.pie(decision_counts.values, labels=decision_counts.index, autopct='%1.1f%%',
                                      colors=['lightcoral', 'lightblue'], startangle=90)
    ax2.set_title(f'Human Decision Distribution\\n({len(overlap_df)} cases)', fontsize=12, fontweight='bold')
    
    # 3. Agreement by test case (top 10)
    ax3 = axes[0, 2]
    test_case_agreement = []
    test_cases = overlap_df['test_case'].value_counts()
    
    for test_case in test_cases.head(10).index:
        subset = overlap_df[overlap_df['test_case'] == test_case]
        if len(subset) > 0:
            agree_rate = (subset['human_false_positive'] == subset['updated_ai_found_issues']).mean()
            test_case_agreement.append((test_case, agree_rate, len(subset)))
    
    # Sort by agreement rate
    test_case_agreement.sort(key=lambda x: x[1], reverse=True)
    
    if test_case_agreement:
        test_names = [x[0].replace('_', ' ').title()[:15] for x in test_case_agreement]
        agree_rates = [x[1] for x in test_case_agreement]
        case_counts = [x[2] for x in test_case_agreement]
        
        bars = ax3.barh(test_names, agree_rates, color='lightgreen', alpha=0.8, edgecolor='black')
        ax3.set_xlabel('Agreement Rate', fontsize=12)
        ax3.set_title('Agreement by Test Case\\n(Top 10 by count)', fontsize=12, fontweight='bold')
        ax3.set_xlim(0, 1)
        
        # Add count labels
        for bar, count in zip(bars, case_counts):
            width = bar.get_width()
            ax3.text(width + 0.02, bar.get_y() + bar.get_height()/2.,
                    f'n={count}', ha='left', va='center', fontsize=9)
    
    # 4. Agreement by jailbreak tactic
    ax4 = axes[1, 0]
    tactic_agreement = []
    tactics = overlap_df['jailbreak_tactic'].value_counts()
    
    for tactic in tactics.index:
        subset = overlap_df[overlap_df['jailbreak_tactic'] == tactic]
        if len(subset) > 0:
            agree_rate = (subset['human_false_positive'] == subset['updated_ai_found_issues']).mean()
            tactic_agreement.append((tactic, agree_rate, len(subset)))
    
    if tactic_agreement:
        tactic_names = [x[0].replace('_', ' ').title() for x in tactic_agreement]
        agree_rates = [x[1] for x in tactic_agreement]
        tactic_counts = [x[2] for x in tactic_agreement]
        
        bars = ax4.bar(tactic_names, agree_rates, color='lightblue', alpha=0.8, edgecolor='black')
        ax4.set_ylabel('Agreement Rate', fontsize=12)
        ax4.set_title('Agreement by Jailbreak Tactic', fontsize=12, fontweight='bold')
        ax4.set_ylim(0, 1)
        plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        # Add count labels
        for bar, count in zip(bars, tactic_counts):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'n={count}', ha='center', va='bottom', fontsize=9)
    
    # 5. Confusion matrix for all cases
    ax5 = axes[1, 1]
    
    both_tp = ((~overlap_df['human_false_positive']) & (~overlap_df['updated_ai_found_issues'])).sum()
    both_fp = (overlap_df['human_false_positive'] & overlap_df['updated_ai_found_issues']).sum()
    human_tp_ai_fp = ((~overlap_df['human_false_positive']) & overlap_df['updated_ai_found_issues']).sum()
    human_fp_ai_tp = (overlap_df['human_false_positive'] & (~overlap_df['updated_ai_found_issues'])).sum()
    
    confusion_matrix = np.array([[both_tp, human_tp_ai_fp], [human_fp_ai_tp, both_fp]])
    sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues', ax=ax5,
                xticklabels=['AI: No Issues', 'AI: Found Issues'],
                yticklabels=['Human: True Pos', 'Human: False Pos'])
    ax5.set_title(f'Updated AI vs Human\\nConfusion Matrix ({len(overlap_df)} cases)', fontsize=12, fontweight='bold')
    
    # 6. Issue detection summary
    ax6 = axes[1, 2]
    
    total_cases = len(overlap_df)
    human_fp_count = overlap_df['human_false_positive'].sum()
    ai_issues_count = overlap_df['updated_ai_found_issues'].sum()
    agreements_count = (overlap_df['human_false_positive'] == overlap_df['updated_ai_found_issues']).sum()
    
    categories = ['Total Cases', 'Human False\\nPositives', 'AI Found\\nIssues', 'Agreements']
    counts = [total_cases, human_fp_count, ai_issues_count, agreements_count]
    colors_summary = ['lightgray', 'lightcoral', 'lightblue', 'lightgreen']
    
    bars = ax6.bar(categories, counts, color=colors_summary, alpha=0.8, edgecolor='black')
    ax6.set_ylabel('Number of Cases', fontsize=12)
    ax6.set_title('Summary Statistics', fontsize=12, fontweight='bold')
    
    # Add count labels
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + total_cases*0.01,
                f'{count}', ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    plt.tight_layout()
    plt.savefig('comprehensive_meta_evaluation_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create detailed CSV for analysis
    overlap_df['agreement'] = overlap_df['human_false_positive'] == overlap_df['updated_ai_found_issues']
    overlap_df.to_csv('comprehensive_human_ai_comparison.csv', index=False)
    
    # Print detailed summary
    print("\\n" + "="*80)
    print("COMPREHENSIVE SUMMARY")
    print("="*80)
    print(f"Total human evaluations available: {len(human_df)}")
    print(f"Total cases with both human and updated AI evaluations: {len(overlap_df)}")
    print(f"Overall agreement rate: {updated_agreement:.1%}")
    print()
    print("Breakdown by decision:")
    decision_breakdown = overlap_df.groupby('decision').agg({
        'agreement': ['count', 'sum', 'mean']
    }).round(3)
    decision_breakdown.columns = ['Total', 'Agreements', 'Agreement_Rate']
    print(decision_breakdown)
    print()
    print("Breakdown by tactic:")
    tactic_breakdown = overlap_df.groupby('jailbreak_tactic').agg({
        'agreement': ['count', 'sum', 'mean']
    }).round(3)
    tactic_breakdown.columns = ['Total', 'Agreements', 'Agreement_Rate'] 
    print(tactic_breakdown.sort_values('Agreement_Rate', ascending=False))
    
    print(f"\\nDetailed results saved to: comprehensive_human_ai_comparison.csv")
    
    return overlap_df

if __name__ == "__main__":
    comprehensive_df = create_comprehensive_comparison()