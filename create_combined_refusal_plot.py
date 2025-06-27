#!/usr/bin/env python3
"""
Create a combined plot showing scratch vs after-refusal sampling distributions
with refused responses treated as score 0.0.

Blue for scratch sampling, orange for after-refusal sampling.
Uses LaTeX fonts and exports as PDF.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy import stats

# Configure matplotlib for LaTeX rendering
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman'],
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.figsize': (10, 6),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1
})

def load_jsonl_metadata(file_path: str) -> Optional[Dict]:
    """Load a JSONL file and extract metadata from the first line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            if first_line:
                metadata = json.loads(first_line)
                return {
                    'jailbreak_tactic': metadata.get('jailbreak_tactic'),
                    'test_case': metadata.get('test_case'),
                    'target_model': metadata.get('target_model'),
                    'turn_type': metadata.get('turn_type'),
                    'timestamp': metadata.get('timestamp'),
                    'sample_id': metadata.get('sample_id', 1)
                }
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def get_all_scores_from_jsonl(file_path: str) -> List:
    """Extract all scores from a JSONL file in order."""
    scores = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        
                        # Skip metadata and goal_achieved entries
                        if 'target_base_url' in entry or 'model_base_url' in entry or 'goal_achieved' in entry:
                            continue
                        
                        # Look for score field
                        if 'score' in entry:
                            score = entry.get('score')
                            if isinstance(score, (int, float)) or score == "refused":
                                scores.append(score)
                                
                    except json.JSONDecodeError:
                        continue
                        
    except (FileNotFoundError, Exception) as e:
        print(f"Error reading file {file_path}: {e}")
        
    return scores

def load_batch_data(batch_path: str, tactic: str, batch_name: str) -> pd.DataFrame:
    """Load batch data for a specific tactic and batch."""
    data_records = []
    
    root_path = Path(batch_path)
    if not root_path.exists():
        print(f"Path not found: {batch_path}")
        return pd.DataFrame()
    
    jsonl_files = list(root_path.rglob('*.jsonl'))
    print(f"Found {len(jsonl_files)} JSONL files in {batch_path}...")
    
    processed_count = 0
    
    for file_path in jsonl_files:
        metadata = load_jsonl_metadata(str(file_path))
        
        if metadata and metadata.get('jailbreak_tactic') == tactic and metadata.get('turn_type') == 'single':
            scores = get_all_scores_from_jsonl(str(file_path))
            
            if scores:
                record = metadata.copy()
                record['file_path'] = str(file_path)
                record['score_sequence'] = scores
                record['n_attempts'] = len(scores)
                record['batch'] = batch_name
                record['tactic'] = tactic
                data_records.append(record)
                processed_count += 1
    
    print(f"Processed {processed_count} files matching criteria ({tactic} + single-turn)")
    return pd.DataFrame(data_records)

def extract_first_and_subsequent_responses(df: pd.DataFrame) -> Tuple[List, List]:
    """Extract first responses (scratch) and subsequent responses (after refusal)."""
    first_responses = []
    subsequent_responses = []
    
    for _, row in df.iterrows():
        scores = row['score_sequence']
        
        if len(scores) > 0:
            first_responses.append(scores[0])
            if len(scores) > 1:
                subsequent_responses.extend(scores[1:])
    
    return first_responses, subsequent_responses

def filter_numeric_only(responses: List) -> List[float]:
    """Extract only numeric scores, excluding 'refused' responses."""
    numeric_scores = []
    
    for response in responses:
        if isinstance(response, (int, float)):
            numeric_scores.append(float(response))
    
    return numeric_scores

def load_all_data():
    """Load all available data combinations."""
    datasets = {}
    
    batch6a_path = 'clean_results/final_runs/batch6A'
    batch6b_path = 'clean_results/final_runs/batch6B'
    
    combinations = [
        ('direct_request', batch6a_path, 'batch6A'),
        ('direct_request', batch6b_path, 'batch6B'),
        ('command', batch6a_path, 'batch6A'),
        ('command', batch6b_path, 'batch6B')
    ]
    
    for tactic, batch_path, batch_name in combinations:
        key = f"{tactic}_{batch_name}"
        print(f"\nLoading {key}...")
        
        df = load_batch_data(batch_path, tactic, batch_name)
        if len(df) > 0:
            datasets[key] = df
            print(f"Successfully loaded {len(df)} conversations")
        else:
            print(f"No data found for {key}")
    
    return datasets

def create_combined_plot():
    """Create the combined plot with all data."""
    print("Loading all data...")
    datasets = load_all_data()
    
    if not datasets:
        print("No data available for plotting")
        return
    
    # Combine all datasets
    all_data = pd.concat(datasets.values(), ignore_index=True)
    print(f"\nCombined data: {len(all_data)} total conversations")
    
    # Extract combined responses
    combined_first, combined_subsequent = extract_first_and_subsequent_responses(all_data)
    
    # Filter to numeric only (exclude refused)
    first_numeric = filter_numeric_only(combined_first)
    subsequent_numeric = filter_numeric_only(combined_subsequent)
    
    print(f"First responses (scratch, numeric only): {len(first_numeric)}")
    print(f"Subsequent responses (after refusal, numeric only): {len(subsequent_numeric)}")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define wider bins (fewer bins for wider appearance)
    bins = np.linspace(0, 1, 11)  # 10 bins instead of 20
    
    # Plot histograms with specified colors - refusal case first (orange)
    # Use weights to get proportion of counts instead of density
    weights_subsequent = np.ones_like(subsequent_numeric) / len(subsequent_numeric)
    weights_first = np.ones_like(first_numeric) / len(first_numeric)
    
    ax.hist(first_numeric, bins=bins, alpha=0.7, color='#ff7f0e', 
            label='refusal', weights=weights_first,
            edgecolor='black', linewidth=0.5)
    
    ax.hist(subsequent_numeric, bins=bins, alpha=0.7, color='#1f77b4', 
            label='sampling', weights=weights_subsequent,
            edgecolor='black', linewidth=0.5)
    
    # Formatting
    ax.set_xlabel('StrongREJECT Score')
    ax.set_ylabel('Proportion')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    
    # Statistical analysis (for console output only)
    if first_numeric and subsequent_numeric:
        # Mann-Whitney U test
        statistic, p_value = stats.mannwhitneyu(first_numeric, subsequent_numeric, alternative='two-sided')
        
        # T-test
        t_stat, t_p_value = stats.ttest_ind(first_numeric, subsequent_numeric)
        
        # Means
        first_mean = np.mean(first_numeric)
        subsequent_mean = np.mean(subsequent_numeric)
    
    plt.tight_layout()
    
    # Save as PDF
    output_file = 'refusal_vs_scratch_combined_plot.pdf'
    plt.savefig(output_file, format='pdf')
    print(f"\nPlot saved as {output_file}")
    
    plt.show()
    
    # Print summary statistics
    print(f"\n{'='*60}")
    print("COMBINED ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    print(f"Total conversations: {len(all_data)}")
    print(f"Scratch sampling responses: {len(first_numeric)}")
    print(f"After-refusal responses: {len(subsequent_numeric)}")
    
    if first_numeric and subsequent_numeric:
        print(f"\nMean scores (numeric only):")
        print(f"  Sampling (scratch): {first_mean:.3f} ± {np.std(first_numeric):.3f}")
        print(f"  Refusal (after refusal): {subsequent_mean:.3f} ± {np.std(subsequent_numeric):.3f}")
        print(f"  Difference: {subsequent_mean - first_mean:+.3f}")
        
        print(f"\nStatistical tests:")
        print(f"  Mann-Whitney U test p-value: {p_value:.6f}")
        print(f"  T-test p-value: {t_p_value:.6f}")
        
        if p_value < 0.05:
            print(f"  Result: Statistically significant difference (p < 0.05)")
        else:
            print(f"  Result: No statistically significant difference (p >= 0.05)")

if __name__ == "__main__":
    create_combined_plot()