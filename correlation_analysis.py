"""
Jailbreak Attack Correlation Analysis

This script analyzes the correlation between different model behaviors when subjected
to jailbreak attacks. It helps understand if models' vulnerabilities to different attack
tactics are correlated, which can provide insights into shared defense mechanisms or
fundamental similarities in how models handle adversarial inputs.

Key features:
- Computation of correlation matrices between models across various attack tactics
- Statistical significance testing of correlations
- Visualization of correlation patterns through heatmaps and cluster analysis
- Export of correlation data to CSV files for further analysis
- Support for various correlation metrics (Pearson, Spearman, etc.)

This analysis is valuable for understanding which models exhibit similar behavior when
faced with jailbreak attempts, potentially revealing common underlying architectures
or training methodologies that lead to similar vulnerabilities or strengths.

Usage:
    python correlation_analysis.py [options]

The script outputs correlation matrices, visualizations, and a summary markdown file
that highlights key findings about model correlations.
"""

import os
import json
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

def extract_scores_from_file(file_path):
    """Extract scores from a jsonl evaluation file"""
    scores = []
    with open(file_path, 'r') as f:
        # Skip the first line (metadata)
        f.readline()
        
        # Read all remaining lines
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if 'score' in data:
                    # Handle case where score is "refused" 
                    if data['score'] == "refused":
                        scores.append(float('nan'))
                    else:
                        try:
                            scores.append(float(data['score']))
                        except (ValueError, TypeError):
                            scores.append(float('nan'))
            except json.JSONDecodeError:
                continue
    
    return scores

def find_original_for_eval_file(eval_file_path):
    """Find the original file for a given evaluation file"""
    pattern = r'(.+)_eval_gpt-4\.1-nano\.jsonl$'
    match = re.match(pattern, eval_file_path)
    if match:
        original_file_path = match.group(1) + ".jsonl"
        if os.path.exists(original_file_path):
            return original_file_path
    return None

def main():
    # Directories to search
    directories = [
        "clean_results/final_runs/batch3A/crowding",
        "clean_results/final_runs/batch3A/direct_request"
    ]
    
    # Store data for correlation analysis
    mini_scores = []
    nano_scores = []
    file_pairs = []
    
    for directory in directories:
        # Get all the nano evaluation files
        nano_files = glob.glob(os.path.join(directory, "*_eval_gpt-4.1-nano.jsonl"))
        
        for nano_file in nano_files:
            # Find the corresponding original file
            original_file = find_original_for_eval_file(nano_file)
            
            if original_file and os.path.exists(original_file):
                # Extract scores from both files
                original_scores = extract_scores_from_file(original_file)
                nano_eval_scores = extract_scores_from_file(nano_file)
                
                # Only use if both have scores and same length
                if original_scores and nano_eval_scores and len(original_scores) == len(nano_eval_scores):
                    # Process pairs of scores, excluding NaN values
                    for i in range(len(original_scores)):
                        if not (np.isnan(original_scores[i]) or np.isnan(nano_eval_scores[i])):
                            mini_scores.append(original_scores[i])
                            nano_scores.append(nano_eval_scores[i])
                    
                    file_pairs.append((original_file, nano_file))
    
    # Convert to numpy arrays for correlation analysis
    mini_scores_np = np.array(mini_scores)
    nano_scores_np = np.array(nano_scores)
    
    # Calculate correlations
    if len(mini_scores_np) > 0 and len(nano_scores_np) > 0:
        pearson_corr, p_value_pearson = pearsonr(mini_scores_np, nano_scores_np)
        spearman_corr, p_value_spearman = spearmanr(mini_scores_np, nano_scores_np)
        
        print(f"Analyzed {len(file_pairs)} file pairs with {len(mini_scores_np)} total valid score pairs")
        print(f"Pearson correlation: {pearson_corr:.4f} (p-value: {p_value_pearson:.4f})")
        print(f"Spearman correlation: {spearman_corr:.4f} (p-value: {p_value_spearman:.4f})")
        
        # Create scatter plot
        plt.figure(figsize=(10, 6))
        plt.scatter(mini_scores_np, nano_scores_np, alpha=0.5)
        plt.xlabel('GPT-4.1-mini Scores (Original Evaluator)')
        plt.ylabel('GPT-4.1-nano Scores')
        plt.title('Correlation between GPT-4.1-mini and GPT-4.1-nano Evaluator Scores')
        
        # Add correlation information as text
        plt.annotate(f"Pearson r: {pearson_corr:.4f} (p: {p_value_pearson:.4f})\nSpearman r: {spearman_corr:.4f} (p: {p_value_spearman:.4f})",
                    xy=(0.05, 0.95), xycoords='axes fraction',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
        
        # Add a line of best fit
        m, b = np.polyfit(mini_scores_np, nano_scores_np, 1)
        plt.plot(mini_scores_np, m*mini_scores_np + b, color='red', linestyle='--')
        
        # Set the axis limits
        score_min = min(mini_scores_np.min(), nano_scores_np.min())
        score_max = max(mini_scores_np.max(), nano_scores_np.max())
        padding = (score_max - score_min) * 0.1  # 10% padding
        plt.xlim(score_min - padding, score_max + padding)
        plt.ylim(score_min - padding, score_max + padding)
        
        # Add a diagonal line (perfect correlation)
        plt.plot([score_min - padding, score_max + padding], 
                [score_min - padding, score_max + padding], 
                'k--', alpha=0.3)
        
        # Save the plot
        plt.grid(True, alpha=0.3)
        plt.savefig('gpt_mini_nano_correlation.png', dpi=300, bbox_inches='tight')
        print("Plot saved as 'gpt_mini_nano_correlation.png'")
    else:
        print("No valid score pairs found for analysis")

if __name__ == "__main__":
    main() 