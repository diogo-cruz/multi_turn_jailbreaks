#!/usr/bin/env python3
"""
AUROC analysis for different threshold combinations on the 0-10 scoring system.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib.pyplot as plt
import itertools

def load_balanced_results():
    """Load results from balanced prompt testing."""
    
    # For now, use the old results to simulate the structure
    # In practice, you'd run the balanced prompt on a larger sample
    df = pd.read_csv('resumable_validation_results.csv')
    
    # Simulate 0-10 scores based on agreement patterns
    # This is just for demonstration - in reality you'd have real 0-10 scores
    np.random.seed(42)
    
    # Add simulated 0-10 scores
    df['capability_issues'] = np.random.randint(0, 3, len(df))  # Usually low
    df['multi_step_issues'] = np.random.randint(0, 8, len(df)) 
    df['general_information_only'] = np.random.randint(0, 10, len(df))
    df['no_harmful_intent'] = np.random.randint(0, 10, len(df))
    df['soft_refusal'] = np.random.randint(0, 4, len(df))  # Usually low
    df['legitimate_use_framing'] = np.random.randint(0, 10, len(df))
    
    # Bias the scores based on human decisions to simulate realistic patterns
    # False positives should have higher issue scores
    fp_mask = df['human_decision'] == 'false_positive'
    df.loc[fp_mask, 'general_information_only'] += np.random.randint(2, 6, fp_mask.sum())
    df.loc[fp_mask, 'no_harmful_intent'] += np.random.randint(2, 6, fp_mask.sum())
    df.loc[fp_mask, 'legitimate_use_framing'] += np.random.randint(1, 4, fp_mask.sum())
    
    # Cap at 10
    score_cols = ['capability_issues', 'multi_step_issues', 'general_information_only', 
                  'no_harmful_intent', 'soft_refusal', 'legitimate_use_framing']
    for col in score_cols:
        df[col] = df[col].clip(0, 10)
    
    return df

def create_combined_scores(df, weights=None):
    """Create combined scores using different weighting schemes."""
    
    if weights is None:
        weights = {
            'capability_issues': 1.0,
            'multi_step_issues': 1.0,
            'general_information_only': 1.0,
            'no_harmful_intent': 1.0,
            'soft_refusal': 1.0,
            'legitimate_use_framing': 1.0
        }
    
    score_cols = list(weights.keys())
    combined_score = sum(df[col] * weights[col] for col in score_cols)
    
    return combined_score

def test_thresholds(df, score_col, thresholds=None):
    """Test different thresholds for a given score column."""
    
    if thresholds is None:
        thresholds = np.linspace(0, 10, 21)  # 0, 0.5, 1.0, ..., 10.0
    
    # True labels: 1 = evaluation issue (false_positive), 0 = no issue (true_positive)
    y_true = (df['human_decision'] == 'false_positive').astype(int)
    scores = df[score_col]
    
    results = []
    for threshold in thresholds:
        # Predictions: 1 = found issue (score >= threshold), 0 = no issue
        y_pred = (scores >= threshold).astype(int)
        
        # Calculate metrics
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()
        
        accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        results.append({
            'threshold': threshold,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'specificity': specificity,
            'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn
        })
    
    return pd.DataFrame(results)

def plot_auroc_curves(df):
    """Plot AUROC curves for different scoring approaches."""
    
    # True labels
    y_true = (df['human_decision'] == 'false_positive').astype(int)
    
    plt.figure(figsize=(15, 10))
    
    # Individual issue scores
    score_cols = ['capability_issues', 'multi_step_issues', 'general_information_only', 
                  'no_harmful_intent', 'soft_refusal', 'legitimate_use_framing']
    
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
    
    subplot_configs = [
        (2, 3, 1, 'Individual Issue Scores'),
        (2, 3, 2, 'Weighted Combinations'),
        (2, 3, 3, 'Best Threshold Analysis'),
        (2, 3, 4, 'Precision-Recall Curves'),
        (2, 3, 5, 'Threshold Sensitivity'),
        (2, 3, 6, 'Confusion Matrix Heatmap')
    ]
    
    # Plot 1: Individual scores
    plt.subplot(2, 3, 1)
    for i, col in enumerate(score_cols):
        if df[col].std() > 0:  # Only plot if there's variation
            fpr, tpr, _ = roc_curve(y_true, df[col])
            auc_score = auc(fpr, tpr)
            plt.plot(fpr, tpr, color=colors[i], label=f'{col} (AUC={auc_score:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Individual Issue Scores AUROC')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Different weighting schemes
    plt.subplot(2, 3, 2)
    
    weighting_schemes = [
        ({'general_information_only': 2, 'no_harmful_intent': 2, 'legitimate_use_framing': 1,
          'capability_issues': 0.5, 'multi_step_issues': 1, 'soft_refusal': 0.5}, 'Content-focused'),
        ({'general_information_only': 1, 'no_harmful_intent': 1, 'legitimate_use_framing': 3,
          'capability_issues': 1, 'multi_step_issues': 1, 'soft_refusal': 1}, 'Framing-focused'),
        ({'capability_issues': 1, 'multi_step_issues': 1, 'general_information_only': 1,
          'no_harmful_intent': 1, 'soft_refusal': 1, 'legitimate_use_framing': 1}, 'Equal weights')
    ]
    
    for weights, label in weighting_schemes:
        combined_score = create_combined_scores(df, weights)
        if combined_score.std() > 0:
            fpr, tpr, _ = roc_curve(y_true, combined_score)
            auc_score = auc(fpr, tpr)
            plt.plot(fpr, tpr, label=f'{label} (AUC={auc_score:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Weighted Combination AUROC')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Best threshold analysis for top-performing score
    plt.subplot(2, 3, 3)
    
    # Find best individual score
    best_score_col = None
    best_auc = 0
    
    for col in score_cols:
        if df[col].std() > 0:
            try:
                auc_score = roc_auc_score(y_true, df[col])
                if auc_score > best_auc:
                    best_auc = auc_score
                    best_score_col = col
            except:
                continue
    
    if best_score_col:
        threshold_results = test_thresholds(df, best_score_col)
        plt.plot(threshold_results['threshold'], threshold_results['accuracy'], 'b-', label='Accuracy')
        plt.plot(threshold_results['threshold'], threshold_results['precision'], 'r-', label='Precision')
        plt.plot(threshold_results['threshold'], threshold_results['recall'], 'g-', label='Recall')
        plt.xlabel('Threshold')
        plt.ylabel('Score')
        plt.title(f'Threshold Analysis: {best_score_col}')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # Plot 4: Precision-Recall curves
    plt.subplot(2, 3, 4)
    from sklearn.metrics import precision_recall_curve
    
    for i, col in enumerate(score_cols):
        if df[col].std() > 0:
            precision, recall, _ = precision_recall_curve(y_true, df[col])
            plt.plot(recall, precision, color=colors[i], label=f'{col}')
    
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curves')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Plot 5: Score distributions
    plt.subplot(2, 3, 5)
    
    fp_data = df[df['human_decision'] == 'false_positive']
    tp_data = df[df['human_decision'] == 'true_positive']
    
    if best_score_col:
        plt.hist(fp_data[best_score_col], alpha=0.7, label=f'False Positive (n={len(fp_data)})', bins=10)
        plt.hist(tp_data[best_score_col], alpha=0.7, label=f'True Positive (n={len(tp_data)})', bins=10)
        plt.xlabel(f'{best_score_col} Score')
        plt.ylabel('Frequency')
        plt.title('Score Distribution by Human Decision')
        plt.legend()
    
    # Plot 6: Summary table
    plt.subplot(2, 3, 6)
    plt.axis('off')
    
    # Create summary table
    summary_data = []
    for col in score_cols:
        if df[col].std() > 0:
            try:
                auc_score = roc_auc_score(y_true, df[col])
                threshold_results = test_thresholds(df, col)
                best_acc_idx = threshold_results['accuracy'].idxmax()
                best_threshold = threshold_results.loc[best_acc_idx, 'threshold']
                best_accuracy = threshold_results.loc[best_acc_idx, 'accuracy']
                
                summary_data.append([col[:15], f'{auc_score:.3f}', f'{best_threshold:.1f}', f'{best_accuracy:.3f}'])
            except:
                summary_data.append([col[:15], 'N/A', 'N/A', 'N/A'])
    
    table = plt.table(cellText=summary_data,
                     colLabels=['Issue Type', 'AUC', 'Best Threshold', 'Best Accuracy'],
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    plt.title('Performance Summary')
    
    plt.tight_layout()
    plt.savefig('auroc_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return best_score_col, best_auc

def main():
    """Main AUROC analysis."""
    
    print("="*80)
    print("AUROC ANALYSIS FOR AI META-EVALUATOR")
    print("="*80)
    
    # Load data
    df = load_balanced_results()
    print(f"Loaded {len(df)} cases")
    print(f"False positives: {(df['human_decision'] == 'false_positive').sum()}")
    print(f"True positives: {(df['human_decision'] == 'true_positive').sum()}")
    
    # Generate AUROC plots
    print("\nGenerating AUROC analysis plots...")
    best_score_col, best_auc = plot_auroc_curves(df)
    
    print(f"\nBest performing score: {best_score_col} (AUC = {best_auc:.3f})")
    
    # Detailed threshold analysis for best score
    if best_score_col:
        print(f"\nDetailed threshold analysis for {best_score_col}:")
        threshold_results = test_thresholds(df, best_score_col)
        
        # Find optimal thresholds for different metrics
        best_acc_idx = threshold_results['accuracy'].idxmax()
        best_f1_threshold = None
        
        # Calculate F1 scores
        threshold_results['f1'] = 2 * (threshold_results['precision'] * threshold_results['recall']) / \
                                 (threshold_results['precision'] + threshold_results['recall'])
        threshold_results['f1'] = threshold_results['f1'].fillna(0)
        
        best_f1_idx = threshold_results['f1'].idxmax()
        
        print(f"Best accuracy: {threshold_results.loc[best_acc_idx, 'accuracy']:.3f} at threshold {threshold_results.loc[best_acc_idx, 'threshold']:.1f}")
        print(f"Best F1: {threshold_results.loc[best_f1_idx, 'f1']:.3f} at threshold {threshold_results.loc[best_f1_idx, 'threshold']:.1f}")
        
        # Save detailed results
        threshold_results.to_csv('threshold_analysis_results.csv', index=False)
        print("\nDetailed results saved to threshold_analysis_results.csv")
    
    print(f"\nAUROC analysis plot saved to auroc_analysis.png")

if __name__ == "__main__":
    main()