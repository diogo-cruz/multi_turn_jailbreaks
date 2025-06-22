#!/usr/bin/env python3
"""
Create comprehensive plots comparing human vs AI meta-evaluator decisions
across different models, tactics, and test cases.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

def load_comprehensive_data():
    """Load comprehensive scores and prepare data for analysis."""
    try:
        df = pd.read_csv('comprehensive_scores_sample.csv')
        return df
    except FileNotFoundError:
        print("No comprehensive scores found. Run collect_comprehensive_scores.py first.")
        return None

def create_human_ai_comparison_plots(df):
    """Create comprehensive comparison plots between human and AI evaluations."""
    
    fig, axes = plt.subplots(4, 3, figsize=(20, 24))
    
    # Plot 1: Overall Agreement Matrix
    ax1 = axes[0, 0]
    
    # Create confusion matrix - need to map ai_found_issues to goal_achieved for clarity
    df['ai_goal_achieved_clear'] = ~df['ai_found_issues']  # Invert for clarity
    agreement_matrix = pd.crosstab(df['human_decision'], df['ai_goal_achieved_clear'], 
                                  rownames=['Human Decision'], colnames=['AI Says Jailbroken'])
    
    sns.heatmap(agreement_matrix, annot=True, fmt='d', cmap='Blues', ax=ax1)
    ax1.set_title('Human vs AI Meta-Evaluator Agreement Matrix')
    ax1.set_xlabel('AI Meta-Evaluator Says Jailbroken')
    ax1.set_ylabel('Human Evaluator Decision')
    
    # Plot 2: Agreement by Test Case
    ax2 = axes[0, 1]
    
    testcase_agreement = df.groupby('test_case').agg({
        'agreement': ['count', 'mean'],
        'human_decision': lambda x: (x == 'true_positive').mean()
    }).round(3)
    
    testcase_agreement.columns = ['count', 'agreement_rate', 'human_jailbreak_rate']
    testcase_agreement = testcase_agreement.sort_values('agreement_rate')
    
    # Only show test cases with at least 3 samples
    testcase_filtered = testcase_agreement[testcase_agreement['count'] >= 3]
    
    bars = ax2.barh(range(len(testcase_filtered)), testcase_filtered['agreement_rate'])
    ax2.set_yticks(range(len(testcase_filtered)))
    ax2.set_yticklabels(testcase_filtered.index, fontsize=8)
    ax2.set_xlabel('Agreement Rate')
    ax2.set_title('Agreement Rate by Test Case (≥3 samples)')
    
    # Color bars by human jailbreak rate
    for i, (bar, rate) in enumerate(zip(bars, testcase_filtered['human_jailbreak_rate'])):
        bar.set_color(plt.cm.RdYlBu_r(rate))
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlBu_r, norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2)
    cbar.set_label('Human Jailbreak Rate')
    
    # Plot 3: Agreement by Jailbreak Tactic
    ax3 = axes[0, 2]
    
    tactic_agreement = df.groupby('tactic').agg({
        'agreement': ['count', 'mean'],
        'human_decision': lambda x: (x == 'true_positive').mean()
    }).round(3)
    
    tactic_agreement.columns = ['count', 'agreement_rate', 'human_jailbreak_rate']
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
    
    # Plot 4: Human vs AI Decision Distribution
    ax4 = axes[1, 0]
    
    decision_counts = pd.crosstab(df['human_decision'], df['ai_goal_achieved_clear'])
    decision_counts.plot(kind='bar', ax=ax4, color=['lightcoral', 'skyblue'])
    ax4.set_title('Distribution of Human vs AI Decisions')
    ax4.set_xlabel('Human Decision')
    ax4.set_ylabel('Count')
    ax4.legend(['AI: Not Jailbroken', 'AI: Jailbroken'])
    ax4.tick_params(axis='x', rotation=45)
    
    # Plot 5: Agreement Rate vs Human Jailbreak Rate by Test Case
    ax5 = axes[1, 1]
    
    # Scatter plot of agreement rate vs human jailbreak rate
    testcase_stats = df.groupby('test_case').agg({
        'agreement': 'mean',
        'human_decision': lambda x: (x == 'true_positive').mean()
    }).reset_index()
    
    testcase_counts = df['test_case'].value_counts()
    testcase_stats['count'] = testcase_stats['test_case'].map(testcase_counts)
    
    # Only include test cases with at least 2 samples
    testcase_stats = testcase_stats[testcase_stats['count'] >= 2]
    
    scatter = ax5.scatter(testcase_stats['human_decision'], testcase_stats['agreement'], 
                         s=testcase_stats['count']*10, alpha=0.6)
    ax5.set_xlabel('Human Jailbreak Rate')
    ax5.set_ylabel('Agreement Rate')
    ax5.set_title('Agreement vs Human Jailbreak Rate by Test Case')
    
    # Add test case labels for interesting points
    for _, row in testcase_stats.iterrows():
        if row['agreement'] < 0.6 or row['agreement'] > 0.9:
            ax5.annotate(row['test_case'][:15], 
                        (row['human_decision'], row['agreement']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Plot 6: Model-specific Analysis (if model info available)
    ax6 = axes[1, 2]
    
    # Extract model info from filename if available
    if 'filename' in df.columns:
        # Try to extract model names from filenames
        df['model'] = df['filename'].str.extract(r'_(gpt-[^_]+|claude-[^_]+|gemini-[^_]+)_')
        
        if df['model'].notna().any():
            model_agreement = df.groupby('model').agg({
                'agreement': ['count', 'mean'],
                'human_decision': lambda x: (x == 'true_positive').mean()
            }).round(3)
            
            model_agreement.columns = ['count', 'agreement_rate', 'human_jailbreak_rate']
            model_agreement = model_agreement[model_agreement['count'] >= 5]  # At least 5 samples
            
            if len(model_agreement) > 0:
                bars = ax6.bar(range(len(model_agreement)), model_agreement['agreement_rate'])
                ax6.set_xticks(range(len(model_agreement)))
                ax6.set_xticklabels(model_agreement.index, rotation=45)
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
            ax6.text(0.5, 0.5, 'No model info extractable', ha='center', va='center', transform=ax6.transAxes)
            ax6.set_title('Model Analysis (No Data)')
    else:
        ax6.text(0.5, 0.5, 'No filename column', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Model Analysis (No Data)')
    
    # Plot 7: Disagreement Analysis - Where Do They Disagree?
    ax7 = axes[2, 0]
    
    disagreements = df[df['agreement'] == False]
    
    if len(disagreements) > 0:
        disagreement_types = []
        for _, row in disagreements.iterrows():
            if row['human_decision'] == 'true_positive' and row['ai_goal_achieved_clear'] == False:
                disagreement_types.append('Human: Jailbroken\\nAI: Not Jailbroken')
            elif row['human_decision'] == 'true_positive' and row['ai_goal_achieved_clear'] == True:
                disagreement_types.append('Human: Jailbroken\\nAI: Jailbroken')
            elif row['human_decision'] == 'false_positive' and row['ai_goal_achieved_clear'] == False:
                disagreement_types.append('Human: Not Jailbroken\\nAI: Not Jailbroken')
            else:
                disagreement_types.append('Human: Not Jailbroken\\nAI: Jailbroken')
        
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
        factor_cols = [
            'general_information_only', 'theoretical_vs_practical', 'incomplete_information',
            'benign_elaboration', 'substitution_deflection', 'topic_drift', 'procedural_deflection',
            'legitimate_use_reframing', 'entertainment_disclaimer', 'educational_justification',
            'hypothetical_framing', 'soft_refusal_mixed_signals', 'capability_overclaim',
            'confusion_misunderstanding', 'rephrasing_issues', 'attacker_failure',
            'multi_step_issues', 'content_gap_score', 'practical_enablement_score',
            'harmful_intent_alignment'
        ]
        
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
        ax8.text(0.5, 0.5, 'No disagreements to analyze', ha='center', va='center', transform=ax8.transAxes)
        ax8.set_title('Factor Analysis for Disagreements')
    
    # Plot 9: Agreement Rate Over Time (if timestamp info available)
    ax9 = axes[2, 2]
    
    # Check if we can extract timestamp info
    if 'filename' in df.columns:
        # Try to extract timestamp from filename
        timestamp_pattern = r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})'
        df['timestamp'] = df['filename'].str.extract(timestamp_pattern)
        
        if df['timestamp'].notna().any():
            # Convert to datetime and group by day
            df['date'] = pd.to_datetime(df['timestamp'], format='%Y_%m_%d_%H_%M_%S', errors='coerce')
            df['date_only'] = df['date'].dt.date
            
            daily_agreement = df.groupby('date_only')['agreement'].agg(['count', 'mean']).reset_index()
            daily_agreement = daily_agreement[daily_agreement['count'] >= 3]  # At least 3 per day
            
            if len(daily_agreement) > 0:
                ax9.plot(daily_agreement['date_only'], daily_agreement['mean'], 'o-')
                ax9.set_xlabel('Date')
                ax9.set_ylabel('Agreement Rate')
                ax9.set_title('Agreement Rate Over Time')
                ax9.tick_params(axis='x', rotation=45)
            else:
                ax9.text(0.5, 0.5, 'Insufficient temporal data', ha='center', va='center', transform=ax9.transAxes)
                ax9.set_title('Agreement Over Time (Insufficient Data)')
        else:
            ax9.text(0.5, 0.5, 'No timestamp extractable', ha='center', va='center', transform=ax9.transAxes)
            ax9.set_title('Agreement Over Time (No Data)')
    else:
        ax9.text(0.5, 0.5, 'No filename column', ha='center', va='center', transform=ax9.transAxes)
        ax9.set_title('Agreement Over Time (No Data)')
    
    # Plot 10: Detailed Test Case Performance Heatmap
    ax10 = axes[3, 0]
    
    # Create a heatmap of test case vs tactic performance
    testcase_tactic = df.groupby(['test_case', 'tactic'])['agreement'].mean().unstack(fill_value=np.nan)
    
    # Only show combinations with at least 1 sample
    mask = testcase_tactic.isna()
    
    if testcase_tactic.shape[0] > 0 and testcase_tactic.shape[1] > 0:
        sns.heatmap(testcase_tactic, annot=False, cmap='RdYlBu_r', mask=mask, 
                   ax=ax10, cbar_kws={'label': 'Agreement Rate'})
        ax10.set_title('Agreement Rate: Test Case vs Tactic')
        ax10.set_xlabel('Jailbreak Tactic')
        ax10.set_ylabel('Test Case')
    else:
        ax10.text(0.5, 0.5, 'Insufficient data for heatmap', ha='center', va='center', transform=ax10.transAxes)
        ax10.set_title('Test Case vs Tactic Heatmap (No Data)')
    
    # Plot 11: Score Distribution Comparison
    ax11 = axes[3, 1]
    
    # Compare score distributions for agreement vs disagreement cases
    agreements = df[df['agreement'] == True]
    disagreements = df[df['agreement'] == False]
    
    if len(disagreements) > 0:
        # Use the best performing factor for comparison
        best_factor = 'harmful_intent_alignment'
        
        if best_factor in df.columns:
            ax11.hist(agreements[best_factor], alpha=0.7, label=f'Agreements (n={len(agreements)})', 
                     bins=10, density=True)
            ax11.hist(disagreements[best_factor], alpha=0.7, label=f'Disagreements (n={len(disagreements)})', 
                     bins=10, density=True)
            ax11.set_xlabel(f'{best_factor} Score')
            ax11.set_ylabel('Density')
            ax11.set_title(f'Score Distribution: {best_factor}')
            ax11.legend()
        else:
            ax11.text(0.5, 0.5, 'Best factor not available', ha='center', va='center', transform=ax11.transAxes)
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
    
    human_jailbroken = (df['human_decision'] == 'true_positive').sum()
    human_not_jailbroken = (df['human_decision'] == 'false_positive').sum()
    
    ai_jailbroken = (df['ai_goal_achieved_clear']).sum()
    ai_not_jailbroken = (~df['ai_goal_achieved_clear']).sum()
    
    # Confusion matrix values (AI agreement with human)
    tp = ((df['human_decision'] == 'true_positive') & (df['ai_goal_achieved_clear'] == True)).sum()   # Both say jailbroken
    tn = ((df['human_decision'] == 'false_positive') & (df['ai_goal_achieved_clear'] == False)).sum()  # Both say not jailbroken
    fp = ((df['human_decision'] == 'false_positive') & (df['ai_goal_achieved_clear'] == True)).sum()   # Human: not jailbroken, AI: jailbroken
    fn = ((df['human_decision'] == 'true_positive') & (df['ai_goal_achieved_clear'] == False)).sum()  # Human: jailbroken, AI: not jailbroken
    
    summary_text = f"""HUMAN vs AI META-EVALUATOR COMPARISON SUMMARY

Total Cases: {total_cases}
Overall Agreement: {agreement_rate:.1%} ({agreements}/{total_cases})

HUMAN EVALUATOR:
  Jailbroken: {human_jailbroken} ({human_jailbroken/total_cases:.1%})
  Not Jailbroken: {human_not_jailbroken} ({human_not_jailbroken/total_cases:.1%})

AI META-EVALUATOR:
  Says Jailbroken: {ai_jailbroken} ({ai_jailbroken/total_cases:.1%})
  Says Not Jailbroken: {ai_not_jailbroken} ({ai_not_jailbroken/total_cases:.1%})

CONFUSION MATRIX (AI Agreement with Human):
  True Positives: {tp} (Both Say Jailbroken)
  True Negatives: {tn} (Both Say Not Jailbroken)
  False Positives: {fp} (Human: Not Jailbroken, AI: Jailbroken)
  False Negatives: {fn} (Human: Jailbroken, AI: Not Jailbroken)

PERFORMANCE METRICS:
  Accuracy: {(tp + tn) / total_cases:.1%}
  Precision: {tp / (tp + fp) if (tp + fp) > 0 else 0:.1%}
  Recall: {tp / (tp + fn) if (tp + fn) > 0 else 0:.1%}
  F1 Score: {2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0:.3f}

UNIQUE TEST CASES: {df['test_case'].nunique()}
UNIQUE TACTICS: {df['tactic'].nunique()}
"""
    
    ax12.text(0.05, 0.95, summary_text, transform=ax12.transAxes, fontsize=9,
             verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('human_ai_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function for human vs AI comparison analysis."""
    
    print("="*80)
    print("HUMAN vs AI META-EVALUATOR COMPARISON ANALYSIS")
    print("="*80)
    
    # Load data
    df = load_comprehensive_data()
    if df is None:
        return
    
    print(f"Loaded {len(df)} cases for comparison analysis")
    print(f"Overall agreement rate: {df['agreement'].mean():.1%}")
    
    # Create comprehensive comparison plots
    print("Generating comprehensive comparison plots...")
    create_human_ai_comparison_plots(df)
    
    print("\\nComparison analysis complete!")
    print("Plots saved to human_ai_comparison_analysis.png")
    
    # Print quick summary by category
    print("\\n" + "="*60)
    print("QUICK BREAKDOWN BY CATEGORY")
    print("="*60)
    
    print("\\nBy Test Case (top/bottom 5):")
    testcase_stats = df.groupby('test_case').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    testcase_stats.columns = ['count', 'agreement_rate']
    testcase_filtered = testcase_stats[testcase_stats['count'] >= 2]
    
    print("Highest agreement:")
    print(testcase_filtered.sort_values('agreement_rate', ascending=False).head())
    print("\\nLowest agreement:")
    print(testcase_filtered.sort_values('agreement_rate', ascending=True).head())
    
    print("\\nBy Jailbreak Tactic:")
    tactic_stats = df.groupby('tactic').agg({
        'agreement': ['count', 'mean']
    }).round(3)
    tactic_stats.columns = ['count', 'agreement_rate']
    print(tactic_stats.sort_values('agreement_rate', ascending=False))

if __name__ == "__main__":
    main()