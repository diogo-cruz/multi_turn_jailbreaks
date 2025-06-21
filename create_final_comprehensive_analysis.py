#!/usr/bin/env python3
"""
Create final comprehensive analysis with all available human and AI meta-evaluation data.
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
    if os.path.exists('complete_77_cases_comparison.csv'):
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

def create_final_comprehensive_analysis():
    """Create comprehensive analysis and plots."""
    
    # Load all data
    human_df = load_all_human_evaluations()
    updated_ai_results = load_all_updated_ai_results()
    
    print(f"\\nTotal human evaluations: {len(human_df)}")
    print(f"Total updated AI results: {len(updated_ai_results)}")
    
    # Find overlap
    overlap_files = set(human_df['filename']) & set(updated_ai_results.keys())
    print(f"Overlapping files (human + updated AI): {len(overlap_files)}")
    
    # Create analysis dataframe
    analysis_df = human_df[human_df['filename'].isin(overlap_files)].copy()
    analysis_df['updated_ai_goal_achieved'] = analysis_df['filename'].map(updated_ai_results)
    analysis_df['updated_ai_found_issues'] = ~analysis_df['updated_ai_goal_achieved']
    analysis_df['human_false_positive'] = analysis_df['decision'] == 'false_positive'
    analysis_df['agreement'] = analysis_df['human_false_positive'] == analysis_df['updated_ai_found_issues']
    
    # Calculate overall agreement
    overall_agreement = analysis_df['agreement'].mean()
    
    print(f"\\n" + "="*80)
    print("FINAL COMPREHENSIVE ANALYSIS")
    print("="*80)
    print(f"Overall Human-AI Agreement: {overall_agreement:.1%}")
    
    # Create comprehensive plots
    fig, axes = plt.subplots(2, 3, figsize=(20, 13))
    fig.suptitle(f'Final Comprehensive Human vs AI Meta-Evaluator Analysis\\n({len(analysis_df)} Cases)', 
                fontsize=18, fontweight='bold')
    
    # 1. Overall agreement visualization
    ax1 = axes[0, 0]
    agreement_data = ['Agreements', 'Disagreements']
    agreement_counts = [analysis_df['agreement'].sum(), (~analysis_df['agreement']).sum()]
    agreement_colors = ['lightgreen', 'lightcoral']
    
    wedges, texts, autotexts = ax1.pie(agreement_counts, labels=agreement_data, autopct='%1.1f%%',
                                      colors=agreement_colors, startangle=90)
    ax1.set_title(f'Overall Agreement\\n({overall_agreement:.1%})', fontsize=14, fontweight='bold')
    
    # 2. Decision distribution
    ax2 = axes[0, 1]
    decision_counts = analysis_df['decision'].value_counts()
    decision_colors = ['lightblue', 'lightcoral']
    
    bars = ax2.bar(decision_counts.index, decision_counts.values, color=decision_colors, alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Number of Cases', fontsize=12)
    ax2.set_title('Human Decision Distribution', fontsize=14, fontweight='bold')
    ax2.set_xticklabels(['True\\nPositive', 'False\\nPositive'])
    
    # Add count labels
    for bar, count in zip(bars, decision_counts.values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{count}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Agreement by test case (top 12)
    ax3 = axes[0, 2]
    test_case_stats = analysis_df.groupby('test_case').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    test_case_stats.columns = ['count', 'agreement_rate']
    test_case_stats = test_case_stats[test_case_stats['count'] >= 3]  # At least 3 cases
    test_case_stats = test_case_stats.sort_values('agreement_rate', ascending=True).tail(12)
    
    y_pos = np.arange(len(test_case_stats))
    test_names = [name.replace('_', ' ').title()[:20] for name in test_case_stats.index]
    
    bars = ax3.barh(y_pos, test_case_stats['agreement_rate'], color='lightblue', alpha=0.8, edgecolor='black')
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(test_names, fontsize=10)
    ax3.set_xlabel('Agreement Rate', fontsize=12)
    ax3.set_title('Agreement by Test Case\\n(≥3 cases, top 12)', fontsize=12, fontweight='bold')
    ax3.set_xlim(0, 1)
    
    # Add count labels
    for bar, count in zip(bars, test_case_stats['count']):
        width = bar.get_width()
        ax3.text(width + 0.02, bar.get_y() + bar.get_height()/2.,
                f'n={int(count)}', ha='left', va='center', fontsize=9)
    
    # 4. Agreement by jailbreak tactic
    ax4 = axes[1, 0]
    tactic_stats = analysis_df.groupby('jailbreak_tactic').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    tactic_stats.columns = ['count', 'agreement_rate']
    tactic_stats = tactic_stats.sort_values('agreement_rate', ascending=False)
    
    tactic_names = [name.replace('_', ' ').title() for name in tactic_stats.index]
    bars = ax4.bar(tactic_names, tactic_stats['agreement_rate'], 
                   color='lightgreen', alpha=0.8, edgecolor='black')
    ax4.set_ylabel('Agreement Rate', fontsize=12)
    ax4.set_title('Agreement by Jailbreak Tactic', fontsize=12, fontweight='bold')
    ax4.set_ylim(0, 1)
    plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
    
    # Add count labels
    for bar, count in zip(bars, tactic_stats['count']):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'n={int(count)}', ha='center', va='bottom', fontsize=9)
    
    # 5. Confusion matrix
    ax5 = axes[1, 1]
    
    both_tp = ((~analysis_df['human_false_positive']) & (~analysis_df['updated_ai_found_issues'])).sum()
    both_fp = (analysis_df['human_false_positive'] & analysis_df['updated_ai_found_issues']).sum()
    human_tp_ai_fp = ((~analysis_df['human_false_positive']) & analysis_df['updated_ai_found_issues']).sum()
    human_fp_ai_tp = (analysis_df['human_false_positive'] & (~analysis_df['updated_ai_found_issues'])).sum()
    
    confusion_matrix = np.array([[both_tp, human_tp_ai_fp], [human_fp_ai_tp, both_fp]])
    
    sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues', ax=ax5,
                xticklabels=['AI: No Issues', 'AI: Found Issues'],
                yticklabels=['Human: True Pos', 'Human: False Pos'],
                cbar_kws={'label': 'Number of Cases'})
    ax5.set_title('Confusion Matrix', fontsize=12, fontweight='bold')
    
    # 6. Agreement trends by model size/type (if data available)
    ax6 = axes[1, 2]
    
    # Extract model information and create categories
    analysis_df['model_family'] = analysis_df['target_model'].str.extract(r'(gpt|claude|gemini)', expand=False)
    analysis_df['model_family'] = analysis_df['model_family'].fillna('other')
    
    model_stats = analysis_df.groupby('model_family').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    model_stats.columns = ['count', 'agreement_rate']
    model_stats = model_stats[model_stats['count'] >= 5]  # At least 5 cases
    
    if len(model_stats) > 0:
        model_names = [name.upper() for name in model_stats.index]
        bars = ax6.bar(model_names, model_stats['agreement_rate'], 
                       color='lightyellow', alpha=0.8, edgecolor='black')
        ax6.set_ylabel('Agreement Rate', fontsize=12)
        ax6.set_title('Agreement by Model Family\\n(≥5 cases)', fontsize=12, fontweight='bold')
        ax6.set_ylim(0, 1)
        
        # Add count labels
        for bar, count in zip(bars, model_stats['count']):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'n={int(count)}', ha='center', va='bottom', fontsize=9)
    else:
        ax6.text(0.5, 0.5, 'Insufficient data\\nfor model comparison', 
                ha='center', va='center', transform=ax6.transAxes, fontsize=12)
        ax6.set_title('Agreement by Model Family', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('final_comprehensive_meta_evaluation_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Generate detailed summary
    print("\\n" + "="*80)
    print("DETAILED BREAKDOWN")
    print("="*80)
    
    print("\\n1. Overall Statistics:")
    print(f"   Total cases analyzed: {len(analysis_df)}")
    print(f"   Agreements: {analysis_df['agreement'].sum()}")
    print(f"   Disagreements: {(~analysis_df['agreement']).sum()}")
    print(f"   Agreement rate: {overall_agreement:.1%}")
    
    print("\\n2. By Human Decision:")
    decision_breakdown = analysis_df.groupby('decision').agg({
        'agreement': ['count', 'sum', 'mean'],
        'updated_ai_found_issues': 'mean'
    }).round(3)
    decision_breakdown.columns = ['Total', 'Agreements', 'Agreement_Rate', 'AI_Found_Issues_Rate']
    print(decision_breakdown)
    
    print("\\n3. By Jailbreak Tactic:")
    tactic_breakdown = analysis_df.groupby('jailbreak_tactic').agg({
        'agreement': ['count', 'sum', 'mean']
    }).round(3)
    tactic_breakdown.columns = ['Total', 'Agreements', 'Agreement_Rate']
    print(tactic_breakdown.sort_values('Agreement_Rate', ascending=False))
    
    print("\\n4. Top Test Cases by Volume (≥5 cases):")
    top_test_cases = analysis_df.groupby('test_case').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    top_test_cases.columns = ['count', 'agreement_rate']
    top_test_cases = top_test_cases[top_test_cases['count'] >= 5].sort_values('count', ascending=False)
    print(top_test_cases.head(10))
    
    # Save detailed results
    analysis_df.to_csv('final_comprehensive_human_ai_comparison.csv', index=False)
    print(f"\\nDetailed results saved to: final_comprehensive_human_ai_comparison.csv")
    
    return analysis_df

if __name__ == "__main__":
    comprehensive_df = create_final_comprehensive_analysis()