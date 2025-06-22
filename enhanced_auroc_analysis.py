#!/usr/bin/env python3
"""
Enhanced AUROC analysis using the 12-factor meta-evaluator system.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns

def load_enhanced_scores():
    """Load enhanced scores from the 12-factor system."""
    try:
        df = pd.read_csv('enhanced_scores_sample.csv')
        return df
    except FileNotFoundError:
        print("No enhanced scores found. Run collect_enhanced_scores.py first.")
        return None

def analyze_individual_factors(df):
    """Analyze performance of individual factors."""
    
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
    
    for col in factor_cols:
        if col in df.columns and df[col].std() > 0:
            try:
                auc_score = roc_auc_score(y_true, df[col])
                
                # Find optimal threshold
                fpr, tpr, thresholds = roc_curve(y_true, df[col])
                optimal_idx = np.argmax(tpr - fpr)
                optimal_threshold = thresholds[optimal_idx]
                
                # Calculate metrics at optimal threshold
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
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
            except Exception as e:
                print(f"Error analyzing {col}: {e}")
                results[col] = None
    
    return results

def test_enhanced_combinations(df):
    """Test different combination strategies for the enhanced factors."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    factor_cols = [
        'general_information_only', 'theoretical_vs_practical', 'incomplete_information',
        'substitution_deflection', 'legitimate_use_reframing', 'entertainment_disclaimer',
        'educational_justification', 'soft_refusal_mixed_signals', 'capability_overclaim',
        'procedural_deflection', 'content_gap_score', 'practical_enablement_score'
    ]
    
    # Enhanced combination strategies
    strategies = {
        'equal_weights': {col: 1.0 for col in factor_cols},
        'content_focused': {
            'general_information_only': 2.0,
            'theoretical_vs_practical': 1.5,
            'incomplete_information': 2.0,
            'substitution_deflection': 1.5,
            'legitimate_use_reframing': 1.0,
            'entertainment_disclaimer': 1.0,
            'educational_justification': 1.0,
            'soft_refusal_mixed_signals': 0.5,
            'capability_overclaim': 0.5,
            'procedural_deflection': 1.0,
            'content_gap_score': 2.5,
            'practical_enablement_score': 2.5
        },
        'gap_enablement_focused': {
            'general_information_only': 1.0,
            'theoretical_vs_practical': 1.0,
            'incomplete_information': 1.0,
            'substitution_deflection': 1.0,
            'legitimate_use_reframing': 1.0,
            'entertainment_disclaimer': 1.0,
            'educational_justification': 1.0,
            'soft_refusal_mixed_signals': 1.0,
            'capability_overclaim': 0.5,
            'procedural_deflection': 1.0,
            'content_gap_score': 3.0,
            'practical_enablement_score': 3.0
        },
        'framing_patterns': {
            'general_information_only': 1.5,
            'theoretical_vs_practical': 1.5,
            'incomplete_information': 1.0,
            'substitution_deflection': 2.0,
            'legitimate_use_reframing': 2.5,
            'entertainment_disclaimer': 2.5,
            'educational_justification': 2.0,
            'soft_refusal_mixed_signals': 1.5,
            'capability_overclaim': 1.0,
            'procedural_deflection': 1.5,
            'content_gap_score': 1.0,
            'practical_enablement_score': 1.0
        },
        'max_score': None,  # Special case - use max of all scores
        'top_3_average': None,  # Special case - average of top 3 scores
    }
    
    combination_results = {}
    
    for strategy_name, weights in strategies.items():
        try:
            if strategy_name == 'max_score':
                # Use maximum score across all factors
                combined_score = df[factor_cols].max(axis=1)
            elif strategy_name == 'top_3_average':
                # Average of top 3 scores for each case
                combined_score = df[factor_cols].apply(lambda row: row.nlargest(3).mean(), axis=1)
            else:
                # Weighted combination
                combined_score = sum(df[col] * weights[col] for col in factor_cols if col in df.columns)
            
            if combined_score.std() > 0:
                auc_score = roc_auc_score(y_true, combined_score)
                
                # Find optimal threshold
                fpr, tpr, thresholds = roc_curve(y_true, combined_score)
                optimal_idx = np.argmax(tpr - fpr)
                optimal_threshold = thresholds[optimal_idx]
                
                combination_results[strategy_name] = {
                    'auc': auc_score,
                    'optimal_threshold': optimal_threshold,
                    'combined_score': combined_score
                }
            
        except Exception as e:
            print(f"Error with strategy {strategy_name}: {e}")
    
    return combination_results

def create_enhanced_plots(df, factor_results, combination_results):
    """Create comprehensive plots for the enhanced analysis."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    fig, axes = plt.subplots(3, 4, figsize=(20, 15))
    
    # Plot 1: Individual factor AUROC curves
    ax1 = axes[0, 0]
    colors = plt.cm.tab20(np.linspace(0, 1, 12))
    
    for i, (factor_name, result) in enumerate(factor_results.items()):
        if result is not None and factor_name in df.columns:
            fpr, tpr, _ = roc_curve(y_true, df[factor_name])
            ax1.plot(fpr, tpr, color=colors[i], 
                    label=f'{factor_name[:12]} (AUC={result["auc"]:.3f})')
    
    ax1.plot([0, 1], [0, 1], 'k--', label='Random')
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('Individual Factors AUROC')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Combination strategies AUROC
    ax2 = axes[0, 1]
    
    for i, (strategy_name, result) in enumerate(combination_results.items()):
        if result is not None:
            fpr, tpr, _ = roc_curve(y_true, result['combined_score'])
            ax2.plot(fpr, tpr, label=f'{strategy_name} (AUC={result["auc"]:.3f})')
    
    ax2.plot([0, 1], [0, 1], 'k--', label='Random')
    ax2.set_xlabel('False Positive Rate')
    ax2.set_ylabel('True Positive Rate')
    ax2.set_title('Combination Strategies AUROC')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Factor correlation heatmap
    ax3 = axes[0, 2]
    factor_cols = [col for col in df.columns if col in factor_results and factor_results[col] is not None]
    if len(factor_cols) > 1:
        corr_matrix = df[factor_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax3, 
                   fmt='.2f', square=True, cbar_kws={"shrink": .8})
        ax3.set_title('Factor Correlations')
        ax3.tick_params(axis='x', rotation=45)
        ax3.tick_params(axis='y', rotation=0)
    
    # Plot 4: Best factor distribution
    ax4 = axes[0, 3]
    best_factor = max(factor_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    best_factor_name = best_factor[0]
    
    if best_factor_name in df.columns:
        fp_scores = df[df['human_decision'] == 'false_positive'][best_factor_name]
        tp_scores = df[df['human_decision'] == 'true_positive'][best_factor_name]
        
        ax4.hist(fp_scores, alpha=0.7, label=f'False Positive (n={len(fp_scores)})', 
                bins=10, color='red')
        ax4.hist(tp_scores, alpha=0.7, label=f'True Positive (n={len(tp_scores)})', 
                bins=10, color='blue')
        ax4.set_xlabel(f'{best_factor_name} Score')
        ax4.set_ylabel('Frequency')
        ax4.set_title(f'Best Factor Distribution: {best_factor_name[:20]}')
        ax4.legend()
    
    # Plot 5-8: Top 4 individual factor performance
    top_4_factors = sorted(factor_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0, reverse=True)[:4]
    
    for i, (factor_name, result) in enumerate(top_4_factors):
        if result is not None:
            ax = axes[1, i]
            
            fp_scores = df[df['human_decision'] == 'false_positive'][factor_name]
            tp_scores = df[df['human_decision'] == 'true_positive'][factor_name]
            
            ax.hist(fp_scores, alpha=0.7, label=f'FP (n={len(fp_scores)})', 
                   bins=8, color='red')
            ax.hist(tp_scores, alpha=0.7, label=f'TP (n={len(tp_scores)})', 
                   bins=8, color='blue')
            ax.set_xlabel('Score')
            ax.set_ylabel('Frequency')
            ax.set_title(f'{factor_name[:15]}\\nAUC={result["auc"]:.3f}')
            ax.legend(fontsize=8)
    
    # Plot 9: Performance summary table
    ax9 = axes[2, 0]
    ax9.axis('off')
    
    # Create summary table
    summary_data = []
    for factor_name, result in factor_results.items():
        if result is not None:
            summary_data.append([
                factor_name[:15],
                f'{result["auc"]:.3f}',
                f'{result["optimal_threshold"]:.1f}',
                f'{result["accuracy"]:.3f}',
                f'{result["f1"]:.3f}'
            ])
    
    # Sort by AUC
    summary_data.sort(key=lambda x: float(x[1]), reverse=True)
    
    if summary_data:
        table = ax9.table(cellText=summary_data[:10],  # Top 10
                         colLabels=['Factor', 'AUC', 'Threshold', 'Accuracy', 'F1'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)
        ax9.set_title('Top Individual Factors Performance')
    
    # Plot 10: Combination strategy comparison
    ax10 = axes[2, 1]
    
    if combination_results:
        strategies = list(combination_results.keys())
        aucs = [combination_results[s]['auc'] for s in strategies]
        
        bars = ax10.bar(range(len(strategies)), aucs, color='skyblue')
        ax10.set_xlabel('Strategy')
        ax10.set_ylabel('AUC')
        ax10.set_title('Combination Strategy Performance')
        ax10.set_xticks(range(len(strategies)))
        ax10.set_xticklabels([s[:10] for s in strategies], rotation=45)
        
        # Add value labels on bars
        for bar, auc in zip(bars, aucs):
            ax10.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                     f'{auc:.3f}', ha='center', va='bottom', fontsize=8)
    
    # Plot 11: Precision-Recall curves for top factors
    ax11 = axes[2, 2]
    
    for i, (factor_name, result) in enumerate(top_4_factors):
        if result is not None and factor_name in df.columns:
            precision, recall, _ = precision_recall_curve(y_true, df[factor_name])
            ax11.plot(recall, precision, color=colors[i], 
                     label=f'{factor_name[:12]}')
    
    ax11.set_xlabel('Recall')
    ax11.set_ylabel('Precision')
    ax11.set_title('Precision-Recall Curves (Top 4)')
    ax11.legend(fontsize=8)
    ax11.grid(True, alpha=0.3)
    
    # Plot 12: Factor importance ranking
    ax12 = axes[2, 3]
    
    factor_names = [name[:15] for name, result in factor_results.items() if result is not None]
    factor_aucs = [result['auc'] for name, result in factor_results.items() if result is not None]
    
    # Sort by AUC
    sorted_indices = np.argsort(factor_aucs)
    sorted_names = [factor_names[i] for i in sorted_indices]
    sorted_aucs = [factor_aucs[i] for i in sorted_indices]
    
    bars = ax12.barh(range(len(sorted_names)), sorted_aucs, color='lightcoral')
    ax12.set_xlabel('AUC')
    ax12.set_title('Factor Importance Ranking')
    ax12.set_yticks(range(len(sorted_names)))
    ax12.set_yticklabels(sorted_names, fontsize=8)
    
    # Add value labels
    for i, (bar, auc) in enumerate(zip(bars, sorted_aucs)):
        ax12.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                 f'{auc:.3f}', ha='left', va='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('enhanced_auroc_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main enhanced AUROC analysis."""
    
    print("="*80)
    print("ENHANCED AUROC ANALYSIS WITH 12-FACTOR SYSTEM")
    print("="*80)
    
    # Load enhanced scores
    df = load_enhanced_scores()
    if df is None:
        print("Run collect_enhanced_scores.py first to collect 12-factor scores")
        return
    
    print(f"Loaded {len(df)} cases with enhanced 12-factor scores")
    print(f"Not jailbroken (human): {(df['human_decision'] == 'false_positive').sum()}")
    print(f"Jailbroken (human): {(df['human_decision'] == 'true_positive').sum()}")
    
    # Analyze individual factors
    print("\\nAnalyzing individual factor performance...")
    factor_results = analyze_individual_factors(df)
    
    # Test combination strategies
    print("Testing enhanced combination strategies...")
    combination_results = test_enhanced_combinations(df)
    
    # Generate comprehensive plots
    print("Generating enhanced analysis plots...")
    create_enhanced_plots(df, factor_results, combination_results)
    
    # Print best results
    print("\\n" + "="*60)
    print("BEST PERFORMING APPROACHES (ENHANCED)")
    print("="*60)
    
    # Best individual factor
    best_individual = max(factor_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    if best_individual[1]:
        print(f"Best individual factor: {best_individual[0]}")
        print(f"  AUC: {best_individual[1]['auc']:.3f}")
        print(f"  Optimal threshold: {best_individual[1]['optimal_threshold']:.1f}")
        print(f"  Accuracy: {best_individual[1]['accuracy']:.3f}")
        print(f"  F1: {best_individual[1]['f1']:.3f}")
    
    # Best combination strategy
    best_combination = max(combination_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    if best_combination[1]:
        print(f"\\nBest combination strategy: {best_combination[0]}")
        print(f"  AUC: {best_combination[1]['auc']:.3f}")
        print(f"  Optimal threshold: {best_combination[1]['optimal_threshold']:.1f}")
    
    # Save detailed results
    results_summary = pd.DataFrame([
        {
            'method': name,
            'type': 'individual',
            'auc': result['auc'],
            'optimal_threshold': result['optimal_threshold'],
            'accuracy': result['accuracy'],
            'f1': result['f1']
        }
        for name, result in factor_results.items() if result is not None
    ])
    
    combination_summary = pd.DataFrame([
        {
            'method': name,
            'type': 'combination',
            'auc': result['auc'],
            'optimal_threshold': result['optimal_threshold'],
            'accuracy': None,  # Would need to calculate
            'f1': None
        }
        for name, result in combination_results.items() if result is not None
    ])
    
    all_results = pd.concat([results_summary, combination_summary], ignore_index=True)
    all_results.to_csv('enhanced_auroc_results.csv', index=False)
    
    print(f"\\nDetailed results saved to enhanced_auroc_results.csv")
    print(f"Enhanced analysis plots saved to enhanced_auroc_analysis.png")

if __name__ == "__main__":
    main()