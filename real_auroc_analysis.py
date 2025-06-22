#!/usr/bin/env python3
"""
Real AUROC analysis using actual 0-10 scores from the balanced prompt.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score, precision_recall_curve
import matplotlib.pyplot as plt
import seaborn as sns

def load_real_scores():
    """Load real 0-10 scores from balanced prompt testing."""
    try:
        df = pd.read_csv('real_scores_sample.csv')
        return df
    except FileNotFoundError:
        print("No real scores found. Run collect_real_scores.py first.")
        return None

def analyze_score_performance(df):
    """Analyze performance of different scoring approaches."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    # Higher meta-evaluator scores should predict "not jailbroken" (0)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    score_cols = ['capability_issues', 'multi_step_issues', 'general_information_only', 
                  'no_harmful_intent', 'soft_refusal', 'legitimate_use_framing']
    
    results = {}
    
    for col in score_cols:
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

def test_combination_strategies(df):
    """Test different combination strategies for the 0-10 scores."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    score_cols = ['capability_issues', 'multi_step_issues', 'general_information_only', 
                  'no_harmful_intent', 'soft_refusal', 'legitimate_use_framing']
    
    # Different combination strategies
    strategies = {
        'simple_sum': {col: 1.0 for col in score_cols},
        'content_focused': {
            'capability_issues': 0.5,
            'multi_step_issues': 1.5,
            'general_information_only': 2.0,
            'no_harmful_intent': 2.0,
            'soft_refusal': 0.5,
            'legitimate_use_framing': 1.0
        },
        'framing_focused': {
            'capability_issues': 0.5,
            'multi_step_issues': 1.0,
            'general_information_only': 1.0,
            'no_harmful_intent': 1.0,
            'soft_refusal': 1.0,
            'legitimate_use_framing': 3.0
        },
        'max_score': None,  # Special case - use max of all scores
        'weighted_average': {
            'capability_issues': 1.0,
            'multi_step_issues': 1.5,
            'general_information_only': 1.8,
            'no_harmful_intent': 1.8,
            'soft_refusal': 0.8,
            'legitimate_use_framing': 1.2
        }
    }
    
    combination_results = {}
    
    for strategy_name, weights in strategies.items():
        try:
            if strategy_name == 'max_score':
                # Use maximum score across all categories
                combined_score = df[score_cols].max(axis=1)
            else:
                # Weighted combination
                combined_score = sum(df[col] * weights[col] for col in score_cols if col in df.columns)
            
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

def create_comprehensive_plots(df, score_results, combination_results):
    """Create comprehensive AUROC analysis plots."""
    
    # True labels: 1 = jailbroken (true_positive), 0 = not jailbroken (false_positive)
    y_true = (df['human_decision'] == 'true_positive').astype(int)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Plot 1: Individual score AUROC curves
    ax1 = axes[0, 0]
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
    
    for i, (score_name, result) in enumerate(score_results.items()):
        if result is not None and score_name in df.columns:
            fpr, tpr, _ = roc_curve(y_true, df[score_name])
            ax1.plot(fpr, tpr, color=colors[i % len(colors)], 
                    label=f'{score_name[:15]} (AUC={result["auc"]:.3f})')
    
    ax1.plot([0, 1], [0, 1], 'k--', label='Random')
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('Individual Scores AUROC')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
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
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Score distributions by human decision
    ax3 = axes[0, 2]
    
    # Find best performing score
    best_score = max(score_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    best_score_name = best_score[0]
    
    if best_score_name in df.columns:
        not_jailbroken_scores = df[df['human_decision'] == 'false_positive'][best_score_name]
        jailbroken_scores = df[df['human_decision'] == 'true_positive'][best_score_name]
        
        ax3.hist(not_jailbroken_scores, alpha=0.7, label=f'Not Jailbroken (n={len(not_jailbroken_scores)})', 
                bins=10, color='red')
        ax3.hist(jailbroken_scores, alpha=0.7, label=f'Jailbroken (n={len(jailbroken_scores)})', 
                bins=10, color='blue')
        ax3.set_xlabel(f'{best_score_name} Score')
        ax3.set_ylabel('Frequency')
        ax3.set_title(f'Score Distribution: {best_score_name}')
        ax3.legend()
    
    # Plot 4: Precision-Recall curves
    ax4 = axes[1, 0]
    
    for i, (score_name, result) in enumerate(score_results.items()):
        if result is not None and score_name in df.columns:
            precision, recall, _ = precision_recall_curve(y_true, df[score_name])
            ax4.plot(recall, precision, color=colors[i % len(colors)], 
                    label=f'{score_name[:15]}')
    
    ax4.set_xlabel('Recall')
    ax4.set_ylabel('Precision')
    ax4.set_title('Precision-Recall Curves')
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Correlation heatmap
    ax5 = axes[1, 1]
    
    score_cols = [col for col in df.columns if col in score_results and score_results[col] is not None]
    if len(score_cols) > 1:
        corr_matrix = df[score_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax5)
        ax5.set_title('Score Correlations')
    
    # Plot 6: Performance summary table
    ax6 = axes[1, 2]
    ax6.axis('off')
    
    # Create summary table
    summary_data = []
    for score_name, result in score_results.items():
        if result is not None:
            summary_data.append([
                score_name[:15],
                f'{result["auc"]:.3f}',
                f'{result["optimal_threshold"]:.1f}',
                f'{result["accuracy"]:.3f}',
                f'{result["f1"]:.3f}'
            ])
    
    # Add combination strategies
    for strategy_name, result in combination_results.items():
        if result is not None:
            # Calculate accuracy and F1 at optimal threshold
            y_pred = (result['combined_score'] >= result['optimal_threshold']).astype(int)
            
            tp = ((y_true == 1) & (y_pred == 1)).sum()
            tn = ((y_true == 0) & (y_pred == 0)).sum()
            fp = ((y_true == 0) & (y_pred == 1)).sum()
            fn = ((y_true == 1) & (y_pred == 0)).sum()
            
            accuracy = (tp + tn) / len(y_true)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            summary_data.append([
                f'{strategy_name}*',
                f'{result["auc"]:.3f}',
                f'{result["optimal_threshold"]:.1f}',
                f'{accuracy:.3f}',
                f'{f1:.3f}'
            ])
    
    if summary_data:
        table = ax6.table(cellText=summary_data,
                         colLabels=['Method', 'AUC', 'Threshold', 'Accuracy', 'F1'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)
        ax6.set_title('Performance Summary\n(* = combination strategy)')
    
    plt.tight_layout()
    plt.savefig('real_auroc_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main real AUROC analysis."""
    
    print("="*80)
    print("REAL AUROC ANALYSIS WITH 0-10 SCORES")
    print("="*80)
    
    # Load real scores
    df = load_real_scores()
    if df is None:
        print("Run collect_real_scores.py first to collect actual 0-10 scores")
        return
    
    print(f"Loaded {len(df)} cases with real 0-10 scores")
    print(f"Not jailbroken (human): {(df['human_decision'] == 'false_positive').sum()}")
    print(f"Jailbroken (human): {(df['human_decision'] == 'true_positive').sum()}")
    
    # Analyze individual score performance
    print("\nAnalyzing individual score performance...")
    score_results = analyze_score_performance(df)
    
    # Test combination strategies
    print("Testing combination strategies...")
    combination_results = test_combination_strategies(df)
    
    # Generate plots
    print("Generating comprehensive plots...")
    create_comprehensive_plots(df, score_results, combination_results)
    
    # Print best results
    print("\n" + "="*60)
    print("BEST PERFORMING APPROACHES")
    print("="*60)
    
    # Best individual score
    best_individual = max(score_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    if best_individual[1]:
        print(f"Best individual score: {best_individual[0]}")
        print(f"  AUC: {best_individual[1]['auc']:.3f}")
        print(f"  Optimal threshold: {best_individual[1]['optimal_threshold']:.1f}")
        print(f"  Accuracy: {best_individual[1]['accuracy']:.3f}")
        print(f"  F1: {best_individual[1]['f1']:.3f}")
    
    # Best combination strategy
    best_combination = max(combination_results.items(), key=lambda x: x[1]['auc'] if x[1] else 0)
    if best_combination[1]:
        print(f"\nBest combination strategy: {best_combination[0]}")
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
        for name, result in score_results.items() if result is not None
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
    all_results.to_csv('auroc_analysis_results.csv', index=False)
    
    print(f"\nDetailed results saved to auroc_analysis_results.csv")
    print(f"Plots saved to real_auroc_analysis.png")

if __name__ == "__main__":
    main()