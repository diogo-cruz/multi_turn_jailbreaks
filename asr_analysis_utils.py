"""
ASR Analysis Utility Functions

This module contains utility functions for Attack Success Rate (ASR) analysis,
including data processing, curve fitting, and visualization functions.
Used by the ASR analysis notebooks for cleaner code organization.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import comb
import os
from pathlib import Path
from typing import Dict, List, Optional
import ast


# ============================================================================
# Data Processing Functions
# ============================================================================

def get_max_score_by_round(data, max_rounds):
    """
    Get the maximum StrongREJECT score over the first r rounds for r = 1 to max_rounds.
    
    Args:
        data: a JSON string containing the attack entries
        max_rounds: Maximum number of rounds to consider
        
    Returns:
        Dictionary with max scores by round (continuous ASR values)
    """
    # Parse data if it's a string
    if isinstance(data, str):
        entries = []
        for line in data.strip().split('\n'):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # For multi-turn, we need to extract scores from evaluation entries after each round
    # Each evaluation entry has a numeric score and corresponds to a round
    evaluation_entries = []
    
    for entry in entries:
        # Skip metadata entry (contains target_base_url, etc.)
        if 'target_base_url' in entry or 'model_base_url' in entry:
            continue
        # Skip goal_achieved entries
        if 'goal_achieved' in entry:
            continue
        # Evaluation entries have numeric score and evaluation metadata
        if 'score' in entry and isinstance(entry.get('score'), (int, float)):
            evaluation_entries.append(entry)
    
    # Calculate max score over first r rounds
    result = {}
    for r in range(1, max_rounds + 1):
        if r <= len(evaluation_entries):
            # Get scores from first r evaluation entries
            scores_up_to_r = [eval_entry['score'] for eval_entry in evaluation_entries[:r]]
            max_score = max(scores_up_to_r) if scores_up_to_r else 0.0
        else:
            # If we don't have r evaluation entries, use all available scores
            all_scores = [eval_entry['score'] for eval_entry in evaluation_entries]
            max_score = max(all_scores) if all_scores else 0.0
        
        result[f'max_score_by_{r}_rounds'] = max_score
    
    return result


def get_max_score_by_round_with_refusals(data, max_rounds):
    """
    Get the maximum StrongREJECT score over the first r rounds, treating refusals as additional rounds with score 0.0.
    This means if there are 8 actual rounds with some refusals, we treat each refusal as adding an extra round.
    
    Args:
        data: a JSON string containing the attack entries
        max_rounds: Maximum number of actual rounds to consider (but we can go beyond this with refusals)
        
    Returns:
        Dictionary with max scores by round (including refusals as 0.0 rounds)
    """
    # Parse data if it's a string
    if isinstance(data, str):
        entries = []
        for line in data.strip().split('\n'):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Extract successful scores and count refusals separately
    successful_scores = []
    refusal_count = 0
    
    for entry in entries:
        # Skip metadata entry
        if 'target_base_url' in entry or 'model_base_url' in entry:
            continue
        # Skip goal_achieved entries
        if 'goal_achieved' in entry:
            continue
        # Look for score field
        if 'score' in entry:
            score = entry.get('score')
            if isinstance(score, (int, float)):
                successful_scores.append(score)
            elif score == "refused":
                refusal_count += 1
    
    # Create extended sequence: successful scores followed by 0.0s for refusals
    all_round_scores = successful_scores + [0.0] * refusal_count
    
    # Calculate max score over first r rounds (including refusals as additional rounds)
    result = {}
    total_rounds = len(all_round_scores)
    
    # Generate scores for all available rounds (not limited by max_rounds for refusal variant)
    for r in range(1, total_rounds + 1):
        scores_up_to_r = all_round_scores[:r]
        max_score = max(scores_up_to_r) if scores_up_to_r else 0.0
        result[f'max_score_by_{r}_rounds'] = max_score
    
    return result


def get_final_score(data):
    """
    Get the final StrongREJECT score from a JSONL conversation.
    For single-turn, this should be the only numeric score.
    
    Args:
        data: a JSON string containing the attack entries
        
    Returns:
        Final StrongREJECT score (float)
    """
    # Parse data if it's a string
    if isinstance(data, str):
        entries = []
        for line in data.strip().split('\n'):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # Look for evaluation entries with numeric scores
    for entry in entries:
        # Skip metadata entry
        if 'target_base_url' in entry or 'model_base_url' in entry:
            continue
        # Skip goal_achieved entries
        if 'goal_achieved' in entry:
            continue
        # Find evaluation entry with numeric score
        if 'score' in entry and isinstance(entry.get('score'), (int, float)):
            return entry.get('score', 0.0)
    
    return 0.0


def get_all_scores_including_refusals(data):
    """
    Get all scores from a single-turn conversation, treating refusals as 0.0.
    
    Args:
        data: a JSON string containing the attack entries
        
    Returns:
        List of scores (float), with refusals converted to 0.0
    """
    # Parse data if it's a string
    if isinstance(data, str):
        entries = []
        for line in data.strip().split('\n'):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    scores = []
    for entry in entries:
        # Skip metadata entry
        if 'target_base_url' in entry or 'model_base_url' in entry:
            continue
        # Skip goal_achieved entries
        if 'goal_achieved' in entry:
            continue
        # Look for score field
        if 'score' in entry:
            score = entry.get('score')
            if isinstance(score, (int, float)):
                scores.append(score)
            elif score == "refused":
                scores.append(0.0)
    
    return scores


def read_json_file(file_path):
    """
    Read a JSON file and return its content.
    """
    with open(file_path, 'r') as file:
        return file.read()


def load_jsonl_metadata(file_path: str) -> Optional[Dict]:
    """
    Load a JSONL file and extract metadata from the first line.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read the first line which contains metadata
            first_line = file.readline().strip()
            if first_line:
                metadata = json.loads(first_line)
                # Extract required fields
                return {
                    'jailbreak_tactic': metadata.get('jailbreak_tactic'),
                    'test_case': metadata.get('test_case'),
                    'target_model': metadata.get('target_model'),
                    'turn_type': metadata.get('turn_type'),
                    'timestamp': metadata.get('timestamp'),
                    'sample_id': metadata.get('sample_id', 1)  # Extract sample_id if available
                }
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"Error processing file {file_path}: {e}")
        return None


def extract_sample_id_from_filename(filename: str) -> int:
    """
    Extract sample ID from filename.
    """
    # Look for pattern like 'sample1', 'sample2', etc.
    import re
    match = re.search(r'sample(\d+)', filename)
    if match:
        return int(match.group(1))
    return 1  # Default to 1 if not found


# ============================================================================
# Mathematical Functions
# ============================================================================

def expected_max_formula(scores, s, n):
    """
    Calculate expected maximum using the theoretical formula.
    This gives us the expected maximum StrongREJECT score from s samples out of n.
    """
    if len(scores) != n:
        return np.nan
    
    # Sort scores to get order statistics
    x_ordered = sorted(scores)
    
    # Calculate expected maximum
    expected_val = 0.0
    for k in range(s, n + 1):
        # x_(k) is the k-th order statistic (1-indexed)
        x_k = x_ordered[k - 1]  # Convert to 0-indexed
        
        # Binomial coefficient C(k-1, s-1)
        binom_coeff = comb(k - 1, s - 1, exact=True)
        
        expected_val += x_k * binom_coeff
    
    # Normalize by C(n, s)
    expected_val /= comb(n, s, exact=True)
    
    return expected_val


# ============================================================================
# Curve Fitting Functions
# ============================================================================

def exponential_approach(x, A, B, c):
    """Exponential approach function: A - B * exp(-c * x)"""
    return A - B * np.exp(-c * x)


def formula(x, A, B, c):
    """Alias for exponential_approach for backward compatibility"""
    return A - B * np.exp(-c * x)


def fit_formula(x_data, y_data):
    """
    Fit the exponential approach model to the data using curve fitting.
    Constrains A and B to be between 0 and 1.
    """
    # Initial guess for parameters A, B, c
    initial_guess = [1.0, 0.5, 0.5]
    
    # Set bounds: A and B between 0 and 1, c can be any positive value
    bounds = ([0, 0, 0], [1, 1, np.inf])
    
    try:
        # Fit the model to the data with bounds
        params, covariance = curve_fit(exponential_approach, x_data, y_data, p0=initial_guess, bounds=bounds)
        return params
    except:
        return None


# ============================================================================
# Styling and Visualization Utilities
# ============================================================================

def get_tactic_style_and_batch_color(tactic, batch, turn_type, batch_name_setting):
    """Return style and color for a given tactic, batch, and turn type"""
    # Base colors: cool for single-turn, warm for multi-turn
    if turn_type == 'single':
        base_color = '#1f77b4'  # blue for single-turn
    else:  # multi-turn
        base_color = '#ff7f0e'  # orange for multi-turn
    
    # Line styles based on batch when plotting both batches
    if batch_name_setting == "both":
        # batch6A = solid lines, batch6B = dashed lines
        if batch == 'batch6A':
            linestyle = '-'  # solid
            batch_label = "Gemini"
        else:  # batch6B
            linestyle = '--'  # dashed
            batch_label = "Claude"
    else:
        # When plotting single batch, tactic determines line style
        if tactic == 'direct_request':
            linestyle = '-'
        else:  # command
            linestyle = '--'
        batch_label = ""
    
    # Marker styles based on tactic
    if tactic == 'direct_request':
        marker = 'o'
    else:  # command
        marker = 's'
    
    return {
        'color': base_color,
        'linestyle': linestyle,
        'marker': marker,
        'markersize': 6,
        'linewidth': 2,
        'batch_label': batch_label
    }


def get_data_range(df, data_type='samples'):
    """
    Get the actual range of data available in the DataFrame.
    
    Args:
        df: DataFrame with score columns
        data_type: 'samples' or 'rounds' to determine column pattern
    
    Returns:
        max_value: Maximum number of samples/rounds with data
    """
    if data_type == 'samples':
        pattern = 'expected_max_score_'
        suffix = '_samples'
    else:  # rounds
        pattern = 'max_score_'
        suffix = '_rounds'
    
    max_value = 0
    for col in df.columns:
        if pattern in col and suffix in col:
            try:
                # Extract the number from column name
                num_str = col.replace(pattern, '').replace(suffix, '')
                num = int(num_str)
                if not df[col].isna().all():  # Only count if column has data
                    max_value = max(max_value, num)
            except:
                continue
    
    return max_value


# ============================================================================
# Main Visualization Functions
# ============================================================================

def plot_combined_analysis(single_turn_results: pd.DataFrame, multi_turn_results: pd.DataFrame, 
                          batch_display_name: str, extend_xaxis: bool, include_command: bool,
                          batch_name_setting: str, figsize=(15, 10), save_path=None):
    """
    Plot combined analysis: single-turn ASR vs samples and multi-turn ASR vs rounds.
    Both use continuous StrongREJECT scores (0-1 range).
    Now supports multiple tactics, batches with different colors, and dynamic x-axis range.
    Fits are excluded from legend but printed to console.
    """
    # Get unique test cases (should be the same for both)
    test_cases = sorted(set(single_turn_results['test_case'].unique()) & 
                       set(multi_turn_results['test_case'].unique()))
    
    # Calculate subplot layout
    n_plots = len(test_cases)
    n_cols = min(3, n_plots)  # Max 3 columns
    n_rows = (n_plots + n_cols - 1) // n_cols  # Ceiling division
    
    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    
    # Handle case where there's only one subplot
    if n_plots == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = axes if n_plots > 1 else [axes]
    else:
        axes = axes.flatten()

    # Determine the maximum range for x-axis across all data
    if extend_xaxis:
        max_samples = get_data_range(single_turn_results, 'samples')
        max_rounds = get_data_range(multi_turn_results, 'rounds')
        max_x = max(max_samples, max_rounds)
    else:
        max_x = 8  # Cap at 8

    # Plot each test case
    for i, test_case in enumerate(test_cases):
        ax = axes[i]
        
        print(f"\n--- Fit parameters for {test_case} ({batch_display_name}) ---")
        
        # Single-turn data (ASR vs samples) - using expected max StrongREJECT scores
        st_data = single_turn_results[single_turn_results['test_case'] == test_case]
        
        for tactic in st_data['jailbreak_tactic'].unique():
            tactic_data = st_data[st_data['jailbreak_tactic'] == tactic]
            
            # Skip if tactic filtering is enabled and this tactic should be excluded
            if not include_command and tactic == 'command':
                continue
            
            # Group by batch if plotting both batches
            if batch_name_setting == "both" and 'batch' in tactic_data.columns:
                batch_groups = tactic_data.groupby('batch')
            else:
                batch_groups = [(batch_name_setting, tactic_data)]
            
            for batch, batch_data in batch_groups:
                if len(batch_data) > 0:
                    st_row = batch_data.iloc[0]
                    style = get_tactic_style_and_batch_color(tactic, batch, 'single', batch_name_setting)
                    
                    # Extract expected max scores by samples (use control variable for range)
                    samples = []
                    asr_scores = []
                    
                    upper_limit = max_x if extend_xaxis else 8
                    for s in range(1, upper_limit + 1):
                        col = f'expected_max_score_{s}_samples'
                        if col in st_row and not pd.isna(st_row[col]):
                            samples.append(s)
                            asr_scores.append(st_row[col])
                    
                    if samples:
                        # Create label
                        if batch_name_setting == "both":
                            label = f'{style["batch_label"]} (single)'
                        else:
                            label = f'{tactic} (single)'
                        
                        ax.scatter(samples, asr_scores, color=style['color'], s=50, alpha=0.7, 
                                  marker=style['marker'], label=label)
                        
                        # Fit curve with higher resolution
                        if len(samples) >= 3:
                            params = fit_formula(np.array(samples), np.array(asr_scores))
                            if params is not None:
                                # Use higher resolution for fit curve with proper line style
                                x_fit = np.linspace(min(samples), max(samples), 100)
                                y_fit = formula(x_fit, *params)
                                ax.plot(x_fit, y_fit, color=style['color'], linewidth=2, alpha=0.7,
                                       linestyle=style['linestyle'])  # Use batch-specific line style for fit
                                print(f"Single-turn {label}: A={params[0]:.3f}, B={params[1]:.3f}, c={params[2]:.3f}")
        
        # Multi-turn data (ASR vs rounds) - using max StrongREJECT scores
        mt_data = multi_turn_results[multi_turn_results['test_case'] == test_case]
        
        for tactic in mt_data['jailbreak_tactic'].unique():
            tactic_data = mt_data[mt_data['jailbreak_tactic'] == tactic]
            
            # Skip if tactic filtering is enabled and this tactic should be excluded
            if not include_command and tactic == 'command':
                continue
            
            # Group by batch if plotting both batches
            if batch_name_setting == "both" and 'batch' in tactic_data.columns:
                batch_groups = tactic_data.groupby('batch')
            else:
                batch_groups = [(batch_name_setting, tactic_data)]
            
            for batch, batch_data in batch_groups:
                if len(batch_data) > 0:
                    mt_row = batch_data.iloc[0]
                    style = get_tactic_style_and_batch_color(tactic, batch, 'multi', batch_name_setting)
                    
                    # Extract max scores by rounds (use control variable for range)
                    rounds = []
                    asr_scores = []
                    
                    upper_limit = max_x if extend_xaxis else 8
                    for r in range(1, upper_limit + 1):
                        col = f'max_score_{r}_rounds'
                        if col in mt_row and not pd.isna(mt_row[col]):
                            rounds.append(r)
                            asr_scores.append(float(mt_row[col]))
                    
                    if rounds:
                        # Create label
                        if batch_name_setting == "both":
                            label = f'{style["batch_label"]} (multi)'
                        else:
                            label = f'{tactic} (multi)'
                        
                        ax.scatter(rounds, asr_scores, color=style['color'], s=50, alpha=0.7, 
                                  marker=style['marker'], label=label)
                        
                        # Fit curve with higher resolution
                        if len(rounds) >= 3:
                            params = fit_formula(np.array(rounds), np.array(asr_scores))
                            if params is not None:
                                # Use higher resolution for fit curve with proper line style
                                x_fit = np.linspace(min(rounds), max(rounds), 100)
                                y_fit = formula(x_fit, *params)
                                ax.plot(x_fit, y_fit, color=style['color'], linewidth=2, alpha=0.7,
                                       linestyle=style['linestyle'])  # Use batch-specific line style for fit
                                print(f"Multi-turn {label}: A={params[0]:.3f}, B={params[1]:.3f}, c={params[2]:.3f}")
        
        # Customize the plot
        ax.set_title(test_case.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.set_xlabel('Number of Samples/Rounds', fontsize=10)
        ax.set_ylabel('ASR (StrongREJECT Score)', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.1)  # StrongREJECT scores between 0 and 1
        ax.legend(fontsize=8, loc='lower right')  # Move legend to bottom right
        
        # Set x-axis ticks based on control variable
        if max_x > 0:
            ax.set_xticks(range(1, max_x + 1))
            ax.set_xlim(0.5, max_x + 0.5)
    
    # Hide unused subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    plt.show()


def plot_averaged_analysis(single_turn_results: pd.DataFrame, multi_turn_results: pd.DataFrame, 
                          batch_display_name: str, extend_xaxis: bool, include_command: bool,
                          batch_name_setting: str, title_suffix: str = "", figsize=(10, 6), save_path=None):
    """
    Plot averaged analysis across all test cases: single-turn ASR vs samples and multi-turn ASR vs rounds.
    Now supports multiple tactics, batches with different colors, error bars, and dynamic x-axis range.
    Fits are excluded from legend but printed to console.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Determine the maximum range for x-axis
    if extend_xaxis:
        max_samples = get_data_range(single_turn_results, 'samples')
        max_rounds = get_data_range(multi_turn_results, 'rounds')
        max_x = max(max_samples, max_rounds)
    else:
        max_x = 8  # Cap at 8
    
    print(f"\n--- Averaged fit parameters ({batch_display_name}){title_suffix} ---")
    
    # Process single-turn data by tactic and batch
    for tactic in single_turn_results['jailbreak_tactic'].unique():
        # Skip if tactic filtering is enabled and this tactic should be excluded
        if not include_command and tactic == 'command':
            continue
            
        tactic_data = single_turn_results[single_turn_results['jailbreak_tactic'] == tactic]
        
        # Group by batch if plotting both batches
        if batch_name_setting == "both" and 'batch' in tactic_data.columns:
            batch_groups = tactic_data.groupby('batch')
        else:
            batch_groups = [(batch_name_setting, tactic_data)]
        
        for batch, batch_data in batch_groups:
            style = get_tactic_style_and_batch_color(tactic, batch, 'single', batch_name_setting)
            
            # Calculate average scores and standard errors across all test cases for this tactic+batch
            single_turn_avg_scores = []
            single_turn_std_errors = []
            samples_range = []
            
            upper_limit = max_x if extend_xaxis else 8
            for s in range(1, upper_limit + 1):
                col = f'expected_max_score_{s}_samples'
                if col in batch_data.columns:
                    scores = batch_data[col].dropna()
                    if len(scores) > 0:
                        avg_score = scores.mean()
                        std_error = scores.std() / np.sqrt(len(scores)) if len(scores) > 1 else 0.0
                        samples_range.append(s)
                        single_turn_avg_scores.append(avg_score)
                        single_turn_std_errors.append(std_error)
            
            # Plot single-turn data points only (no connecting lines)
            if samples_range:
                # Create label
                if batch_name_setting == "both":
                    label = f'{style["batch_label"]} (single)'
                else:
                    label = f'{tactic} (single)'
                
                # Plot data points with error bars but no connecting lines
                ax.errorbar(samples_range, single_turn_avg_scores, yerr=single_turn_std_errors,
                           color=style['color'], fmt=style['marker'], markersize=8, alpha=0.8, capsize=5,
                           linestyle='None', linewidth=0,  # No connecting lines for data points
                           label=label, zorder=5)
                
                # Fit curve for single-turn with higher resolution
                if len(samples_range) >= 3:
                    params = fit_formula(np.array(samples_range), np.array(single_turn_avg_scores))
                    if params is not None:
                        # Use higher resolution for fit curve with proper line style
                        x_fit = np.linspace(min(samples_range), max(samples_range), 100)
                        y_fit = formula(x_fit, *params)
                        ax.plot(x_fit, y_fit, color=style['color'], linewidth=3, alpha=0.8,
                               linestyle=style['linestyle'])  # Use batch-specific line style for fit
                        print(f"Single-turn {label}: A={params[0]:.3f}, B={params[1]:.3f}, c={params[2]:.3f}")
    
    # Process multi-turn data by tactic and batch
    for tactic in multi_turn_results['jailbreak_tactic'].unique():
        # Skip if tactic filtering is enabled and this tactic should be excluded
        if not include_command and tactic == 'command':
            continue
            
        tactic_data = multi_turn_results[multi_turn_results['jailbreak_tactic'] == tactic]
        
        # Group by batch if plotting both batches
        if batch_name_setting == "both" and 'batch' in tactic_data.columns:
            batch_groups = tactic_data.groupby('batch')
        else:
            batch_groups = [(batch_name_setting, tactic_data)]
        
        for batch, batch_data in batch_groups:
            style = get_tactic_style_and_batch_color(tactic, batch, 'multi', batch_name_setting)
            
            # Calculate average scores and standard errors across all test cases for this tactic+batch
            multi_turn_avg_scores = []
            multi_turn_std_errors = []
            rounds_range = []
            
            upper_limit = max_x if extend_xaxis else 8
            for r in range(1, upper_limit + 1):
                col = f'max_score_{r}_rounds'
                if col in batch_data.columns:
                    scores = batch_data[col].dropna()
                    if len(scores) > 0:
                        avg_score = scores.mean()
                        std_error = scores.std() / np.sqrt(len(scores)) if len(scores) > 1 else 0.0
                        rounds_range.append(r)
                        multi_turn_avg_scores.append(avg_score)
                        multi_turn_std_errors.append(std_error)
            
            # Plot multi-turn data points only (no connecting lines)
            if rounds_range:
                # Create label
                if batch_name_setting == "both":
                    label = f'{style["batch_label"]} (multi)'
                else:
                    label = f'{tactic} (multi)'
                
                # Plot data points with error bars but no connecting lines
                ax.errorbar(rounds_range, multi_turn_avg_scores, yerr=multi_turn_std_errors,
                           color=style['color'], fmt=style['marker'], markersize=8, alpha=0.8, capsize=5,
                           linestyle='None', linewidth=0,  # No connecting lines for data points
                           label=label, zorder=5)
                
                # Fit curve for multi-turn with higher resolution
                if len(rounds_range) >= 3:
                    params = fit_formula(np.array(rounds_range), np.array(multi_turn_avg_scores))
                    if params is not None:
                        # Use higher resolution for fit curve with proper line style
                        x_fit = np.linspace(min(rounds_range), max(rounds_range), 100)
                        y_fit = formula(x_fit, *params)
                        ax.plot(x_fit, y_fit, color=style['color'], linewidth=3, alpha=0.8,
                               linestyle=style['linestyle'])  # Use batch-specific line style for fit
                        print(f"Multi-turn {label}: A={params[0]:.3f}, B={params[1]:.3f}, c={params[2]:.3f}")
    
    # Customize the plot
    ax.set_title(f'Average ASR vs Samples/Rounds ({batch_display_name}){title_suffix}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Number of Samples/Rounds', fontsize=12)
    ax.set_ylabel('Average ASR (StrongREJECT Score)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)  # StrongREJECT scores between 0 and 1
    ax.legend(fontsize=10, loc='lower right')  # Move legend to bottom right
    
    # Set x-axis ticks based on control variable
    if max_x > 0:
        ax.set_xticks(range(1, max_x + 1))
        ax.set_xlim(0.5, max_x + 0.5)
    
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    plt.show()