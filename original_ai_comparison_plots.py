#!/usr/bin/env python3
"""
Create comprehensive plots comparing original goal_achieved evaluations vs AI meta-evaluator decisions
across different models, tactics, and test cases.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def load_comparison_data():
    """Load original vs AI comparison data."""
    try:
        # Try to load from the comparison file created by compare_original_ai_evaluations.py
        df = pd.read_csv('original_ai_comparison.csv')
        return df
    except FileNotFoundError:
        print("No original_ai_comparison.csv found. Run compare_original_ai_evaluations.py first.")
        return None

def create_original_ai_comparison_plots(df):
    """Create comprehensive comparison plots between original and AI meta-evaluations."""
    
    fig, axes = plt.subplots(4, 3, figsize=(20, 24))
    
    # Plot 1: Overall Agreement Matrix
    ax1 = axes[0, 0]
    
    # Create confusion matrix
    agreement_matrix = pd.crosstab(df['original_goal_achieved'], df['ai_found_issues'], 
                                  rownames=['Original: Goal Achieved'], colnames=['AI Meta: Found Issues'])
    
    sns.heatmap(agreement_matrix, annot=True, fmt='d', cmap='Blues', ax=ax1)
    ax1.set_title('Original vs AI Meta-Evaluator Agreement Matrix')
    ax1.set_xlabel('AI Meta-Evaluator Found Issues')
    ax1.set_ylabel('Original Evaluation: Goal Achieved')
    
    # Plot 2: Agreement by Test Case
    ax2 = axes[0, 1]
    
    # Check if test case data is available in any column name variation
    test_case_col = None
    for col in ['test_case', 'test_case_original']:
        if col in df.columns:
            test_case_col = col
            break
    
    if test_case_col:
        testcase_agreement = df.groupby(test_case_col).agg({
            'agreement': ['count', 'mean'],
            'original_goal_achieved': 'mean'
        }).round(3)
        
        testcase_agreement.columns = ['count', 'agreement_rate', 'original_jailbreak_rate']
        testcase_agreement = testcase_agreement.sort_values('agreement_rate')
        
        # Only show test cases with at least 3 samples
        testcase_filtered = testcase_agreement[testcase_agreement['count'] >= 3]
        
        if len(testcase_filtered) > 0:
            bars = ax2.barh(range(len(testcase_filtered)), testcase_filtered['agreement_rate'])
            ax2.set_yticks(range(len(testcase_filtered)))
            ax2.set_yticklabels(testcase_filtered.index, fontsize=8)
            ax2.set_xlabel('Agreement Rate')
            ax2.set_title('Agreement Rate by Test Case (≥3 samples)')
            
            # Color bars by original jailbreak rate
            for i, (bar, rate) in enumerate(zip(bars, testcase_filtered['original_jailbreak_rate'])):
                bar.set_color(plt.cm.RdYlBu_r(rate))
            
            # Add colorbar
            sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlBu_r, norm=plt.Normalize(0, 1))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax2)
            cbar.set_label('Original Jailbreak Rate')
        else:
            ax2.text(0.5, 0.5, 'Insufficient test case data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Agreement Rate by Test Case')
    else:
        ax2.text(0.5, 0.5, 'Test case data not available', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Agreement Rate by Test Case')
    
    # Plot 3: Agreement by Jailbreak Tactic
    ax3 = axes[0, 2]
    
    # Check if tactic data is available in any column name variation
    tactic_col = None
    for col in ['tactic', 'jailbreak_tactic', 'jailbreak_tactic_original']:
        if col in df.columns:
            tactic_col = col
            break
    
    if tactic_col:
        tactic_agreement = df.groupby(tactic_col).agg({
            'agreement': ['count', 'mean'],
            'original_goal_achieved': 'mean'
        }).round(3)
        
        tactic_agreement.columns = ['count', 'agreement_rate', 'original_jailbreak_rate']
        tactic_agreement = tactic_agreement.sort_values('agreement_rate')
        
        bars = ax3.bar(range(len(tactic_agreement)), tactic_agreement['agreement_rate'])
        ax3.set_xticks(range(len(tactic_agreement)))
        ax3.set_xticklabels(tactic_agreement.index, rotation=45)
        ax3.set_ylabel('Agreement Rate')
        ax3.set_title('Agreement Rate by Jailbreak Tactic')
        
        # Add count labels on bars
        for bar, count, rate in zip(bars, tactic_agreement['count'], tactic_agreement['agreement_rate']):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'n={count}', ha='center', va='bottom', fontsize=8)
    else:
        ax3.text(0.5, 0.5, 'Tactic data not available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Agreement Rate by Jailbreak Tactic')
    
    # Plot 4: Original vs AI Decision Distribution
    ax4 = axes[1, 0]
    
    decision_counts = pd.crosstab(df['original_goal_achieved'], df['ai_found_issues'])
    decision_counts.plot(kind='bar', ax=ax4, color=['lightcoral', 'skyblue'])
    ax4.set_title('Distribution of Original vs AI Meta Decisions')
    ax4.set_xlabel('Original: Goal Achieved')
    ax4.set_ylabel('Count')
    ax4.legend(['AI: No Issues Found', 'AI: Issues Found'])
    ax4.tick_params(axis='x', rotation=45)
    
    # Plot 5: Agreement Rate vs Original Jailbreak Rate by Test Case
    ax5 = axes[1, 1]
    
    if 'test_case_original' in df.columns:
        # Scatter plot of agreement rate vs original jailbreak rate
        testcase_stats = df.groupby('test_case_original').agg({
            'agreement': 'mean',
            'original_goal_achieved': 'mean'
        }).reset_index()
        
        testcase_counts = df['test_case_original'].value_counts()
        testcase_stats['count'] = testcase_stats['test_case_original'].map(testcase_counts)
        
        # Only include test cases with at least 2 samples
        testcase_stats = testcase_stats[testcase_stats['count'] >= 2]
        
        if len(testcase_stats) > 0:
            scatter = ax5.scatter(testcase_stats['original_goal_achieved'], testcase_stats['agreement'], 
                                 s=testcase_stats['count']*10, alpha=0.6)
            ax5.set_xlabel('Original Jailbreak Rate')
            ax5.set_ylabel('Agreement Rate')
            ax5.set_title('Agreement vs Original Jailbreak Rate by Test Case')
            
            # Add test case labels for interesting points
            for _, row in testcase_stats.iterrows():
                if row['agreement'] < 0.6 or row['agreement'] > 0.9:
                    ax5.annotate(row['test_case_original'][:15], 
                                (row['original_goal_achieved'], row['agreement']),
                                xytext=(5, 5), textcoords='offset points', fontsize=8)
        else:
            ax5.text(0.5, 0.5, 'Insufficient test case data', ha='center', va='center', transform=ax5.transAxes)
            ax5.set_title('Agreement vs Original Jailbreak Rate')
    else:
        ax5.text(0.5, 0.5, 'Test case data not available', ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Agreement vs Original Jailbreak Rate')
    
    # Plot 6: Model-specific Analysis
    ax6 = axes[1, 2]
    
    # Check if model data is available
    model_col = None
    for col in ['target_model', 'target_model_original']:
        if col in df.columns:
            model_col = col
            break
    
    if model_col:
        model_agreement = df.groupby(model_col).agg({
            'agreement': ['count', 'mean'],
            'original_goal_achieved': 'mean'
        }).round(3)
        
        model_agreement.columns = ['count', 'agreement_rate', 'original_jailbreak_rate']
        model_agreement = model_agreement[model_agreement['count'] >= 5]  # At least 5 samples
        
        if len(model_agreement) > 0:
            bars = ax6.bar(range(len(model_agreement)), model_agreement['agreement_rate'])
            ax6.set_xticks(range(len(model_agreement)))
            ax6.set_xticklabels(model_agreement.index, rotation=45, ha='right')
            ax6.set_ylabel('Agreement Rate')
            ax6.set_title('Agreement Rate by Target Model (≥5 samples)')
            
            # Add count labels
            for bar, count in zip(bars, model_agreement['count']):
                ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'n={count}', ha='center', va='bottom', fontsize=8)
        else:
            ax6.text(0.5, 0.5, 'Insufficient model data', ha='center', va='center', transform=ax6.transAxes)
            ax6.set_title('Model Analysis (Insufficient Data)')
    else:
        ax6.text(0.5, 0.5, 'Model data not available', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Model Analysis (No Data)')
    
    # Plot 7: Disagreement Analysis
    ax7 = axes[2, 0]
    
    disagreements = df[df['agreement'] == False]
    
    if len(disagreements) > 0:
        disagreement_types = []
        for _, row in disagreements.iterrows():
            if row['original_goal_achieved'] == True and row['ai_found_issues'] == True:
                disagreement_types.append('Original: Goal Achieved\\nAI: Found Issues')
            elif row['original_goal_achieved'] == True and row['ai_found_issues'] == False:
                disagreement_types.append('Original: Goal Achieved\\nAI: No Issues')
            elif row['original_goal_achieved'] == False and row['ai_found_issues'] == True:
                disagreement_types.append('Original: Goal Not Achieved\\nAI: Found Issues')
            else:
                disagreement_types.append('Original: Goal Not Achieved\\nAI: No Issues')
        
        disagreement_counts = Counter(disagreement_types)
        
        bars = ax7.bar(range(len(disagreement_counts)), list(disagreement_counts.values()))
        ax7.set_xticks(range(len(disagreement_counts)))
        ax7.set_xticklabels(list(disagreement_counts.keys()), rotation=45, ha='right')
        ax7.set_ylabel('Count')
        ax7.set_title(f'Types of Disagreements (n={len(disagreements)})')
        
        # Add value labels
        for bar, count in zip(bars, disagreement_counts.values()):
            ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom')
    else:
        ax7.text(0.5, 0.5, 'No disagreements found', ha='center', va='center', transform=ax7.transAxes)
        ax7.set_title('Disagreement Analysis')
    
    # Plot 8: Top Scoring Factors for Disagreements
    ax8 = axes[2, 1]
    
    if len(disagreements) > 0:
        # Find issue/score columns
        factor_cols = [col for col in df.columns if 'issue' in col.lower() or col.endswith('_score')]
        factor_cols = [col for col in factor_cols if df[col].dtype in ['float64', 'int64']]
        
        if len(factor_cols) > 0:
            # Calculate mean scores for disagreement cases vs agreement cases
            disagreement_means = disagreements[factor_cols].mean()
            agreement_means = df[df['agreement'] == True][factor_cols].mean()
            
            # Find factors with biggest differences
            differences = (disagreement_means - agreement_means).abs().sort_values(ascending=False)
            top_diff_factors = differences.head(10)
            
            disagreement_top = disagreement_means[top_diff_factors.index]
            agreement_top = agreement_means[top_diff_factors.index]
            
            x = np.arange(len(top_diff_factors))
            width = 0.35
            
            ax8.bar(x - width/2, disagreement_top, width, label='Disagreements', alpha=0.7)
            ax8.bar(x + width/2, agreement_top, width, label='Agreements', alpha=0.7)
            
            ax8.set_xlabel('Factors')
            ax8.set_ylabel('Mean Score')
            ax8.set_title('Top Discriminating Factors (Disagreement vs Agreement)')
            ax8.set_xticks(x)
            ax8.set_xticklabels([f[:12] for f in top_diff_factors.index], rotation=45, ha='right')
            ax8.legend()
        else:
            ax8.text(0.5, 0.5, 'No factor columns found', ha='center', va='center', transform=ax8.transAxes)
            ax8.set_title('Factor Analysis for Disagreements')
    else:
        ax8.text(0.5, 0.5, 'No disagreements to analyze', ha='center', va='center', transform=ax8.transAxes)
        ax8.set_title('Factor Analysis for Disagreements')
    
    # Plot 9: Agreement Rate by Original Evaluator Model
    ax9 = axes[2, 2]
    
    if 'evaluator_model' in df.columns:
        evaluator_agreement = df.groupby('evaluator_model').agg({
            'agreement': ['count', 'mean'],
            'original_goal_achieved': 'mean'
        }).round(3)
        
        evaluator_agreement.columns = ['count', 'agreement_rate', 'original_jailbreak_rate']
        evaluator_agreement = evaluator_agreement[evaluator_agreement['count'] >= 3]
        
        if len(evaluator_agreement) > 0:
            bars = ax9.bar(range(len(evaluator_agreement)), evaluator_agreement['agreement_rate'])
            ax9.set_xticks(range(len(evaluator_agreement)))
            ax9.set_xticklabels(evaluator_agreement.index, rotation=45, ha='right')
            ax9.set_ylabel('Agreement Rate')
            ax9.set_title('Agreement Rate by Original Evaluator Model')
            
            # Add count labels
            for bar, count in zip(bars, evaluator_agreement['count']):
                ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'n={count}', ha='center', va='bottom', fontsize=8)
        else:
            ax9.text(0.5, 0.5, 'Insufficient evaluator data', ha='center', va='center', transform=ax9.transAxes)
            ax9.set_title('Agreement by Original Evaluator')
    else:
        ax9.text(0.5, 0.5, 'Evaluator data not available', ha='center', va='center', transform=ax9.transAxes)
        ax9.set_title('Agreement by Original Evaluator')
    
    # Plot 10: Test Case vs Tactic Heatmap
    ax10 = axes[3, 0]
    
    if 'test_case_original' in df.columns and 'jailbreak_tactic_original' in df.columns:
        testcase_tactic = df.groupby(['test_case_original', 'jailbreak_tactic_original'])['agreement'].mean().unstack(fill_value=np.nan)
        
        mask = testcase_tactic.isna()
        
        if testcase_tactic.shape[0] > 0 and testcase_tactic.shape[1] > 0:
            sns.heatmap(testcase_tactic, annot=False, cmap='RdYlBu_r', mask=mask, 
                       ax=ax10, cbar_kws={'label': 'Agreement Rate'})
            ax10.set_title('Agreement Rate: Test Case vs Tactic')
            ax10.set_xlabel('Jailbreak Tactic')
            ax10.set_ylabel('Test Case')
        else:
            ax10.text(0.5, 0.5, 'Insufficient data for heatmap', ha='center', va='center', transform=ax10.transAxes)
            ax10.set_title('Test Case vs Tactic Heatmap')
    else:
        ax10.text(0.5, 0.5, 'Test case/tactic data not available', ha='center', va='center', transform=ax10.transAxes)
        ax10.set_title('Test Case vs Tactic Heatmap')
    
    # Plot 11: Score Distribution Comparison
    ax11 = axes[3, 1]
    
    agreements = df[df['agreement'] == True]
    disagreements = df[df['agreement'] == False]
    
    if len(disagreements) > 0:
        # Find a good factor for comparison
        factor_cols = [col for col in df.columns if 'issue' in col.lower() or col.endswith('_score')]
        factor_cols = [col for col in factor_cols if df[col].dtype in ['float64', 'int64']]
        
        if len(factor_cols) > 0:
            best_factor = factor_cols[0]  # Use first available factor
            
            ax11.hist(agreements[best_factor], alpha=0.7, label=f'Agreements (n={len(agreements)})', 
                     bins=10, density=True)
            ax11.hist(disagreements[best_factor], alpha=0.7, label=f'Disagreements (n={len(disagreements)})', 
                     bins=10, density=True)
            ax11.set_xlabel(f'{best_factor} Score')
            ax11.set_ylabel('Density')
            ax11.set_title(f'Score Distribution: {best_factor}')
            ax11.legend()
        else:
            ax11.text(0.5, 0.5, 'No factor data available', ha='center', va='center', transform=ax11.transAxes)
            ax11.set_title('Score Distribution Comparison')
    else:
        ax11.text(0.5, 0.5, 'No disagreements to compare', ha='center', va='center', transform=ax11.transAxes)
        ax11.set_title('Score Distribution Comparison')
    
    # Plot 12: Summary Statistics Table
    ax12 = axes[3, 2]
    ax12.axis('off')
    
    # Calculate comprehensive summary statistics
    total_cases = len(df)
    agreements = (df['agreement']).sum()
    agreement_rate = agreements / total_cases
    
    original_jailbroken = (df['original_goal_achieved']).sum()
    original_not_jailbroken = (~df['original_goal_achieved']).sum()
    
    ai_found_issues = (df['ai_found_issues']).sum()
    ai_no_issues = (~df['ai_found_issues']).sum()
    
    # Confusion matrix values
    # Agreement when: original_goal_achieved=True AND ai_found_issues=False, OR original_goal_achieved=False AND ai_found_issues=True
    tp = ((df['original_goal_achieved'] == True) & (df['ai_found_issues'] == False)).sum()   # Original jailbroken, AI agrees (no issues found)
    tn = ((df['original_goal_achieved'] == False) & (df['ai_found_issues'] == True)).sum()  # Original not jailbroken, AI agrees (issues found)
    fp = ((df['original_goal_achieved'] == False) & (df['ai_found_issues'] == False)).sum()   # Original not jailbroken, AI disagrees (no issues found)
    fn = ((df['original_goal_achieved'] == True) & (df['ai_found_issues'] == True)).sum()  # Original jailbroken, AI disagrees (issues found)
    
    summary_text = f"""ORIGINAL vs AI META-EVALUATOR COMPARISON SUMMARY

Total Cases: {total_cases}
Overall Agreement: {agreement_rate:.1%} ({agreements}/{total_cases})

ORIGINAL EVALUATOR:
  Goal Achieved: {original_jailbroken} ({original_jailbroken/total_cases:.1%})
  Goal Not Achieved: {original_not_jailbroken} ({original_not_jailbroken/total_cases:.1%})

AI META-EVALUATOR:
  Found Issues: {ai_found_issues} ({ai_found_issues/total_cases:.1%})
  No Issues Found: {ai_no_issues} ({ai_no_issues/total_cases:.1%})

CONFUSION MATRIX (AI Agreement with Original):
  True Positives: {tp} (Original: Jailbroken, AI: No Issues)
  True Negatives: {tn} (Original: Not Jailbroken, AI: Found Issues)
  False Positives: {fp} (Original: Not Jailbroken, AI: No Issues)
  False Negatives: {fn} (Original: Jailbroken, AI: Found Issues)

PERFORMANCE METRICS:
  Accuracy: {(tp + tn) / total_cases:.1%}
  Precision: {tp / (tp + fp) if (tp + fp) > 0 else 0:.1%}
  Recall: {tp / (tp + fn) if (tp + fn) > 0 else 0:.1%}
  F1 Score: {2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0:.3f}
"""
    
    if 'test_case_original' in df.columns:
        summary_text += f"\nUNIQUE TEST CASES: {df['test_case_original'].nunique()}"
    if 'jailbreak_tactic_original' in df.columns:
        summary_text += f"\nUNIQUE TACTICS: {df['jailbreak_tactic_original'].nunique()}"
    
    ax12.text(0.05, 0.95, summary_text, transform=ax12.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('original_ai_comparison_analysis.png', dpi=300, bbox_inches='tight')
    print("Comprehensive plot saved as original_ai_comparison_analysis.png")
    plt.show()

def main():
    """Main function for original vs AI meta-evaluator comparison analysis."""
    
    print("="*80)
    print("ORIGINAL vs AI META-EVALUATOR COMPARISON ANALYSIS")
    print("="*80)
    
    # Load data
    df = load_comparison_data()
    if df is None:
        return
    
    print(f"Loaded {len(df)} cases for comparison analysis")
    print(f"Overall agreement rate: {df['agreement'].mean():.1%}")
    
    # Create comprehensive comparison plots
    print("Generating comprehensive comparison plots...")
    create_original_ai_comparison_plots(df)
    
    print("\nComparison analysis complete!")
    print("Plots saved to original_ai_comparison_analysis.png")
    
    # Print quick summary by category
    print("\n" + "="*60)
    print("QUICK BREAKDOWN BY CATEGORY")
    print("="*60)
    
    if 'test_case_original' in df.columns:
        print("\nBy Test Case (top/bottom 5):")
        testcase_stats = df.groupby('test_case_original').agg({
            'agreement': ['count', 'mean']
        }).round(3)
        testcase_stats.columns = ['count', 'agreement_rate']
        testcase_filtered = testcase_stats[testcase_stats['count'] >= 2]
        
        if len(testcase_filtered) > 0:
            print("Highest agreement:")
            print(testcase_filtered.sort_values('agreement_rate', ascending=False).head())
            print("\nLowest agreement:")
            print(testcase_filtered.sort_values('agreement_rate', ascending=True).head())
    
    if 'jailbreak_tactic_original' in df.columns:
        print("\nBy Jailbreak Tactic:")
        tactic_stats = df.groupby('jailbreak_tactic_original').agg({
            'agreement': ['count', 'mean']
        }).round(3)
        tactic_stats.columns = ['count', 'agreement_rate']
        print(tactic_stats.sort_values('agreement_rate', ascending=False))

if __name__ == "__main__":
    main()