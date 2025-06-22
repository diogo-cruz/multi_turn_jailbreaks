#!/usr/bin/env python3
"""
Simulate enhanced AUROC analysis to demonstrate the 12-factor approach.
Uses the existing real scores data with expanded factors.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib.pyplot as plt

def simulate_enhanced_factors():
    """Create simulated enhanced factor data from existing real scores."""
    
    # Load existing real scores
    df = pd.read_csv('real_scores_sample.csv')
    
    # Keep the original 6 factors but rename them to match enhanced system
    df_enhanced = df.copy()
    
    # Map old factors to new enhanced factors
    df_enhanced = df_enhanced.rename(columns={
        'multi_step_issues': 'incomplete_information',
        'no_harmful_intent': 'theoretical_vs_practical', 
        'soft_refusal': 'soft_refusal_mixed_signals',
        'legitimate_use_framing': 'legitimate_use_reframing'
    })
    
    # Add 6 new simulated factors based on patterns in existing data
    np.random.seed(42)
    
    # Create correlated factors based on existing patterns
    df_enhanced['substitution_deflection'] = np.clip(
        df_enhanced['general_information_only'] * 0.7 + np.random.normal(0, 2, len(df_enhanced)), 0, 10)
    
    df_enhanced['entertainment_disclaimer'] = np.clip(
        df_enhanced['legitimate_use_reframing'] * 0.4 + np.random.normal(0, 2, len(df_enhanced)), 0, 10)
    
    df_enhanced['educational_justification'] = np.clip(
        df_enhanced['general_information_only'] * 0.6 + np.random.normal(0, 2, len(df_enhanced)), 0, 10)
    
    df_enhanced['capability_overclaim'] = np.clip(
        np.random.normal(1, 1.5, len(df_enhanced)), 0, 10)  # Usually low
    
    df_enhanced['procedural_deflection'] = np.clip(
        df_enhanced['theoretical_vs_practical'] * 0.5 + np.random.normal(0, 2, len(df_enhanced)), 0, 10)
    
    # Add combination scores that should perform well
    df_enhanced['content_gap_score'] = np.clip(
        (df_enhanced['general_information_only'] + df_enhanced['theoretical_vs_practical']) / 2 + 
        np.random.normal(0, 1, len(df_enhanced)), 0, 10)
    
    df_enhanced['practical_enablement_score'] = np.clip(
        10 - (df_enhanced['general_information_only'] + df_enhanced['incomplete_information']) / 2 + 
        np.random.normal(0, 1, len(df_enhanced)), 0, 10)
    
    # Round to integers
    factor_cols = [
        'general_information_only', 'theoretical_vs_practical', 'incomplete_information',
        'substitution_deflection', 'legitimate_use_reframing', 'entertainment_disclaimer',
        'educational_justification', 'soft_refusal_mixed_signals', 'capability_overclaim',
        'procedural_deflection', 'content_gap_score', 'practical_enablement_score'
    ]
    
    for col in factor_cols:
        df_enhanced[col] = df_enhanced[col].round().astype(int).clip(0, 10)
    
    return df_enhanced

def analyze_simulated_performance():
    """Analyze the simulated enhanced factor performance."""
    
    df = simulate_enhanced_factors()
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    # Higher meta-evaluator scores should predict "not jailbroken" (0)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    factor_cols = [
        'general_information_only', 'theoretical_vs_practical', 'incomplete_information',
        'substitution_deflection', 'legitimate_use_reframing', 'entertainment_disclaimer',
        'educational_justification', 'soft_refusal_mixed_signals', 'capability_overclaim',
        'procedural_deflection', 'content_gap_score', 'practical_enablement_score'
    ]
    
    results = {}
    
    print("="*80)
    print("SIMULATED ENHANCED AUROC ANALYSIS (12-FACTOR DEMONSTRATION)")
    print("="*80)
    print(f"Dataset size: {len(df)} cases")
    print(f"Not jailbroken (human): {(df['human_decision'] == 'false_positive').sum()}")
    print(f"Jailbroken (human): {(df['human_decision'] == 'true_positive').sum()}")
    
    # Analyze each factor
    for col in factor_cols:
        if col in df.columns and df[col].std() > 0:
            try:
                auc_score = roc_auc_score(y_true, df[col])
                fpr, tpr, thresholds = roc_curve(y_true, df[col])
                optimal_idx = np.argmax(tpr - fpr)
                optimal_threshold = thresholds[optimal_idx]
                
                y_pred = (df[col] >= optimal_threshold).astype(int)
                tp = ((y_true == 1) & (y_pred == 1)).sum()
                tn = ((y_true == 0) & (y_pred == 0)).sum()
                fp = ((y_true == 0) & (y_pred == 1)).sum()
                fn = ((y_true == 1) & (y_pred == 0)).sum()
                
                accuracy = (tp + tn) / len(y_true)
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                results[col] = {
                    'auc': auc_score,
                    'optimal_threshold': optimal_threshold,
                    'accuracy': accuracy,
                    'f1': f1
                }
                
            except Exception as e:
                print(f"Error analyzing {col}: {e}")
    
    # Print results sorted by AUC
    print(f"\\n{'Factor':<25} {'AUC':<6} {'Threshold':<10} {'Accuracy':<9} {'F1':<6}")
    print("-" * 70)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['auc'], reverse=True)
    for factor_name, result in sorted_results:
        print(f"{factor_name:<25} {result['auc']:<6.3f} {result['optimal_threshold']:<10.1f} "
              f"{result['accuracy']:<9.3f} {result['f1']:<6.3f}")
    
    # Test combination strategies
    print(f"\\n" + "="*60)
    print("COMBINATION STRATEGY PERFORMANCE")
    print("="*60)
    
    strategies = {
        'equal_weights': {col: 1.0 for col in factor_cols},
        'content_gap_focused': {
            col: 3.0 if 'content_gap' in col or 'practical_enablement' in col else 1.0 
            for col in factor_cols
        },
        'top_individual_focused': {
            col: 2.0 if col in [sorted_results[0][0], sorted_results[1][0], sorted_results[2][0]] else 0.5
            for col in factor_cols
        }
    }
    
    for strategy_name, weights in strategies.items():
        combined_score = sum(df[col] * weights[col] for col in factor_cols if col in df.columns)
        if combined_score.std() > 0:
            auc_score = roc_auc_score(y_true, combined_score)
            print(f"{strategy_name:<25} AUC: {auc_score:.3f}")
    
    # Create visualization
    create_enhanced_visualization(df, results, sorted_results)
    
    print(f"\\nSimulated enhanced analysis complete!")
    print("This demonstrates the potential of the 12-factor approach.")
    print("Run collect_enhanced_scores.py to get real data from the enhanced prompt.")
    
    return df, results

def create_enhanced_visualization(df, results, sorted_results):
    """Create visualization for the simulated enhanced analysis."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Plot 1: Top 6 factors AUROC
    ax1 = axes[0, 0]
    colors = plt.cm.tab10(np.linspace(0, 1, 6))
    
    for i, (factor_name, result) in enumerate(sorted_results[:6]):
        if factor_name in df.columns:
            fpr, tpr, _ = roc_curve(y_true, df[factor_name])
            ax1.plot(fpr, tpr, color=colors[i], 
                    label=f'{factor_name[:15]} ({result["auc"]:.3f})')
    
    ax1.plot([0, 1], [0, 1], 'k--', label='Random')
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('Top 6 Factors AUROC (Simulated)')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Factor performance ranking
    ax2 = axes[0, 1]
    
    factor_names = [name[:15] for name, _ in sorted_results]
    factor_aucs = [result['auc'] for _, result in sorted_results]
    
    bars = ax2.barh(range(len(factor_names)), factor_aucs, color='lightcoral')
    ax2.set_xlabel('AUC')
    ax2.set_title('Enhanced Factor Performance Ranking')
    ax2.set_yticks(range(len(factor_names)))
    ax2.set_yticklabels(factor_names)
    
    for i, (bar, auc) in enumerate(zip(bars, factor_aucs)):
        ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{auc:.3f}', ha='left', va='center')
    
    # Plot 3: Best factor distribution
    ax3 = axes[0, 2]
    best_factor_name = sorted_results[0][0]
    
    not_jailbroken_scores = df[df['human_decision'] == 'false_positive'][best_factor_name]
    jailbroken_scores = df[df['human_decision'] == 'true_positive'][best_factor_name]
    
    ax3.hist(not_jailbroken_scores, alpha=0.7, label=f'Not Jailbroken (n={len(not_jailbroken_scores)})', 
            bins=8, color='red')
    ax3.hist(jailbroken_scores, alpha=0.7, label=f'Jailbroken (n={len(jailbroken_scores)})', 
            bins=8, color='blue')
    ax3.set_xlabel(f'{best_factor_name} Score')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'Best Factor: {best_factor_name[:20]}')
    ax3.legend()
    
    # Plot 4: Factor correlation heatmap
    ax4 = axes[1, 0]
    factor_cols = [name for name, _ in sorted_results[:8]]  # Top 8 for visibility
    corr_matrix = df[factor_cols].corr()
    
    import seaborn as sns
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax4, 
               fmt='.2f', square=True)
    ax4.set_title('Factor Correlations (Top 8)')
    ax4.tick_params(axis='x', rotation=45)
    ax4.tick_params(axis='y', rotation=0)
    
    # Plot 5: Enhanced vs Original comparison
    ax5 = axes[1, 1]
    
    # Compare with original 6-factor performance
    original_factors = ['general_information_only', 'theoretical_vs_practical', 
                       'incomplete_information', 'legitimate_use_reframing',
                       'soft_refusal_mixed_signals']
    new_factors = ['substitution_deflection', 'entertainment_disclaimer',
                  'educational_justification', 'capability_overclaim',
                  'procedural_deflection', 'content_gap_score', 'practical_enablement_score']
    
    orig_aucs = [results[f]['auc'] for f in original_factors if f in results]
    new_aucs = [results[f]['auc'] for f in new_factors if f in results]
    
    ax5.boxplot([orig_aucs, new_aucs], labels=['Original\\nFactors', 'Enhanced\\nFactors'])
    ax5.set_ylabel('AUC')
    ax5.set_title('Original vs Enhanced Factors')
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Performance summary
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    summary_text = f"""ENHANCED ANALYSIS SUMMARY

Top 3 Factors:
1. {sorted_results[0][0][:20]}: {sorted_results[0][1]['auc']:.3f}
2. {sorted_results[1][0][:20]}: {sorted_results[1][1]['auc']:.3f}  
3. {sorted_results[2][0][:20]}: {sorted_results[2][1]['auc']:.3f}

Average AUC:
All factors: {np.mean([r[1]['auc'] for r in sorted_results]):.3f}
Top 6: {np.mean([r[1]['auc'] for r in sorted_results[:6]]):.3f}

Best Threshold: {sorted_results[0][1]['optimal_threshold']:.1f}
Best Accuracy: {sorted_results[0][1]['accuracy']:.3f}
Best F1: {sorted_results[0][1]['f1']:.3f}
"""
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('simulated_enhanced_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    df, results = analyze_simulated_performance()