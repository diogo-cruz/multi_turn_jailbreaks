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

# Set up matplotlib to use LaTeX
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.size': 24,
    'axes.labelsize': 24,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 18
})


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
    
    # If no evaluation entries found, return empty result (conversation failed)
    if not evaluation_entries:
        return {}
    
    # Calculate max score over first r rounds
    result = {}
    
    # First, calculate the actual max scores for available rounds
    available_max_scores = []
    for r in range(1, len(evaluation_entries) + 1):
        scores_up_to_r = [eval_entry['score'] for eval_entry in evaluation_entries[:r]]
        max_score = max(scores_up_to_r) if scores_up_to_r else 0.0
        available_max_scores.append(max_score)
    
    # Now generate results for all requested rounds, extending the last value if needed
    for r in range(1, max_rounds + 1):
        if r <= len(available_max_scores):
            # Use actual calculated max score
            result[f'max_score_by_{r}_rounds'] = available_max_scores[r - 1]
        else:
            # Extend with the last available max score
            result[f'max_score_by_{r}_rounds'] = available_max_scores[-1] if available_max_scores else 0.0
    
    return result


def get_max_score_by_round_with_refusals(data, max_rounds):
    """
    Get the maximum StrongREJECT score over the first r rounds, treating refusals as additional rounds with score 0.0.
    This preserves the chronological order of refusals and numeric scores.
    
    Args:
        data: a JSON string containing the attack entries
        max_rounds: Maximum number of actual rounds to consider (but we can go beyond this with refusals)
        
    Returns:
        Dictionary with max scores by round (including refusals as 0.0 rounds in chronological order)
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

    # Collect all scoring entries (both numeric and refusals) in chronological order
    round_scores = []
    
    for entry in entries:
        # Skip metadata entry (contains target_base_url, etc.)
        if 'target_base_url' in entry or 'model_base_url' in entry:
            continue
        # Skip goal_achieved entries
        if 'goal_achieved' in entry:
            continue
        
        # Look for entries with score field
        if 'score' in entry:
            score_value = entry.get('score')
            round_num = entry.get('round', None)  # Try to get round number if available
            
            if score_value == "refused":
                # Refusal counts as 0.0 score
                round_scores.append({
                    'round': round_num,
                    'score': 0.0,
                    'type': 'refusal'
                })
            elif isinstance(score_value, (int, float)):
                # Numeric score
                round_scores.append({
                    'round': round_num,
                    'score': float(score_value),
                    'type': 'numeric'
                })
    
    # Sort by round number if available, otherwise preserve order from file
    if all(entry['round'] is not None for entry in round_scores):
        round_scores.sort(key=lambda x: x['round'])
    
    # Extract just the scores in chronological order
    all_round_scores = [entry['score'] for entry in round_scores]
    
    # If no scoring entries found, return empty result (conversation failed)
    if not all_round_scores:
        return {}
    
    # Calculate max score over first r rounds (including refusals as 0.0 in proper order)
    result = {}
    total_rounds = len(all_round_scores)
    
    # First, calculate the actual max scores for available rounds
    available_max_scores = []
    for r in range(1, total_rounds + 1):
        scores_up_to_r = all_round_scores[:r]
        max_score = max(scores_up_to_r) if scores_up_to_r else 0.0
        available_max_scores.append(max_score)
    
    # Generate scores for requested rounds, extending if we have fewer rounds than max_rounds
    max_rounds_to_generate = max(max_rounds, total_rounds)
    for r in range(1, max_rounds_to_generate + 1):
        if r <= len(available_max_scores):
            # Use actual calculated max score
            result[f'max_score_by_{r}_rounds'] = available_max_scores[r - 1]
        else:
            # Extend with the last available max score
            result[f'max_score_by_{r}_rounds'] = available_max_scores[-1] if available_max_scores else 0.0
    
    return result


def get_final_score(data):
    """
    Get the final StrongREJECT score from a JSONL conversation.
    For single-turn, this should be the only numeric score.
    
    Args:
        data: a JSON string containing the attack entries
        
    Returns:
        Final StrongREJECT score (float) or None if no score found
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
    
    return None  # Return None if no score found (empty conversation)


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
    
    # Line styles and batch labels based on batch when plotting multiple batches
    if batch_name_setting == "both":
        # batch6A = solid lines, batch6B = dashed lines
        if batch == 'batch6A':
            linestyle = '-'  # solid
            batch_label = "Gemini"
        else:  # batch6B
            linestyle = '--'  # dashed
            batch_label = "Claude"
    elif batch_name_setting == "all":
        # batch6A = solid, batch6B = dashed, batch6C = dotted
        if batch == 'batch6A':
            linestyle = '-'  # solid
            batch_label = "Gemini (6A)"
        elif batch == 'batch6B':
            linestyle = '--'  # dashed
            batch_label = "Claude (6B)"
        else:  # batch6C
            linestyle = ':'  # dotted
            batch_label = "Batch6C"
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


def determine_plotting_range(single_turn_df, multi_turn_df, single_turn_with_refusals_df, multi_turn_with_refusals_df, 
                           extend_xaxis_for_refusals, max_samples_param, max_rounds_param):
    """
    Determine the actual plotting range that will be used based on available data and settings.
    
    Returns:
        tuple: (max_samples_plotting, max_rounds_plotting, max_samples_plotting_ref, max_rounds_plotting_ref)
    """
    if extend_xaxis_for_refusals:
        # For extended axis, we need to check the raw data to see maximum available
        # For single-turn with refusals, check the maximum number of attempts across all test cases
        max_samples_plotting = 8  # default
        max_rounds_plotting = 8   # default
        max_samples_plotting_ref = 8
        max_rounds_plotting_ref = 8
        
        if len(single_turn_with_refusals_df) > 0:
            # Group by test case and find max samples available
            group_cols = ['test_case', 'target_model', 'jailbreak_tactic']
            if 'batch' in single_turn_with_refusals_df.columns:
                group_cols.append('batch')
            
            grouped = single_turn_with_refusals_df.groupby(group_cols)
            max_samples_per_group = []
            for _, group in grouped:
                max_samples_per_group.append(len(group))
            
            if max_samples_per_group:
                max_samples_plotting_ref = max(max_samples_per_group)
                max_samples_plotting = min(max_samples_plotting_ref, 8)  # Original variant capped at available or 8
        
        if len(multi_turn_with_refusals_df) > 0:
            # For multi-turn, we need to check the raw data for maximum rounds including refusals
            max_rounds_available = []
            for _, row in multi_turn_with_refusals_df.iterrows():
                # Count columns that have data
                round_count = 0
                for col in row.index:
                    if 'max_score_by_' in col and '_rounds' in col:
                        try:
                            round_num = int(col.replace('max_score_by_', '').replace('_rounds', ''))
                            if not pd.isna(row[col]):
                                round_count = max(round_count, round_num)
                        except:
                            continue
                if round_count > 0:
                    max_rounds_available.append(round_count)
            
            if max_rounds_available:
                max_rounds_plotting_ref = max(max_rounds_available)
                max_rounds_plotting = min(max_rounds_plotting_ref, 8)  # Original variant capped at 8
    else:
        # For non-extended axis, use fixed values
        max_samples_plotting = 8
        max_rounds_plotting = 8
        max_samples_plotting_ref = 8
        max_rounds_plotting_ref = 8
    
    return max_samples_plotting, max_rounds_plotting, max_samples_plotting_ref, max_rounds_plotting_ref


# ============================================================================
# Data Analysis Functions
# ============================================================================

def extract_batch_metadata(batch_paths: List[str], max_rounds: int = 8, include_command: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Extract metadata from batch files, separating single-turn and multi-turn data.
    Now supports multiple batches and tactics filtering.
    
    Args:
        batch_paths: List of directory paths to search for JSONL files
        max_rounds: Maximum number of rounds to analyze for multi-turn
        
    Returns:
        Dictionary with 'single_turn', 'single_turn_with_refusals', 'multi_turn', and 'multi_turn_with_refusals' DataFrames
    """
    single_turn_data = []
    single_turn_with_refusals_data = []  # Include refusals as 0.0 scores
    multi_turn_data = []
    multi_turn_with_refusals_data = []  # Include refusals as 0.0 rounds
    
    # Determine which tactics to include based on the include_command parameter
    tactics_to_include = ['direct_request']
    if include_command:
        tactics_to_include.append('command')
    
    processed_count = 0
    tactic_counts = {}
    batch_counts = {}
    
    for batch_path in batch_paths:
        batch_name = Path(batch_path).name  # Extract batch name from path
        batch_counts[batch_name] = 0
        
        # Use pathlib to recursively find all .jsonl files
        root_path = Path(batch_path)
        jsonl_files = list(root_path.rglob('*.jsonl'))
        
        print(f"Found {len(jsonl_files)} JSONL files in {batch_name}...")
        
        for file_path in jsonl_files:
            metadata = load_jsonl_metadata(str(file_path))
            if metadata:
                tactic = metadata.get('jailbreak_tactic')
                
                # Process files with selected tactics
                if tactic in tactics_to_include:
                    # Count tactics and batches
                    tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
                    batch_counts[batch_name] += 1
                    
                    # Add the file path and batch info for reference
                    metadata['file_path'] = str(file_path)
                    metadata['batch'] = batch_name
                    
                    # Extract sample ID from filename if not in metadata
                    if 'sample_id' not in metadata or metadata['sample_id'] is None:
                        metadata['sample_id'] = extract_sample_id_from_filename(file_path.name)
                    
                    # Read the file data
                    data = read_json_file(str(file_path))
                    
                    if metadata.get('turn_type') == 'single':
                        # For single-turn, get the final StrongREJECT score from evaluation entry
                        final_score = get_final_score(data)
                        all_scores = get_all_scores_including_refusals(data)
                        
                        # Only include if there's actual scoring data (not just metadata)
                        if final_score is not None or all_scores:
                            if final_score is not None:
                                metadata['final_score'] = final_score
                                single_turn_data.append(metadata.copy())
                            
                            # Also get all scores including refusals for the alternative analysis
                            if all_scores:
                                for i, score in enumerate(all_scores):
                                    refusal_metadata = metadata.copy()
                                    refusal_metadata['final_score'] = score
                                    refusal_metadata['sample_id'] = f"{metadata['sample_id']}_attempt_{i+1}"
                                    single_turn_with_refusals_data.append(refusal_metadata)
                        else:
                            print(f"Skipping empty single-turn conversation: {file_path}")
                        
                    elif metadata.get('turn_type') == 'multi':
                        # For multi-turn, get scores by rounds (original method)
                        round_scores = get_max_score_by_round(data, max_rounds)
                        
                        # Check if this conversation actually has any rounds (not just metadata)
                        has_actual_rounds = any(f'max_score_by_{r}_rounds' in round_scores 
                                              for r in range(1, max_rounds + 1) 
                                              if round_scores.get(f'max_score_by_{r}_rounds') is not None)
                        
                        if has_actual_rounds:
                            metadata_original = metadata.copy()
                            metadata_original.update(round_scores)
                            multi_turn_data.append(metadata_original)
                            
                            # Also get scores by rounds including refusals as 0.0
                            round_scores_with_refusals = get_max_score_by_round_with_refusals(data, max_rounds)
                            
                            # Check if the refusal variant also has actual data
                            if round_scores_with_refusals:
                                metadata_with_refusals = metadata.copy()
                                metadata_with_refusals.update(round_scores_with_refusals)
                                multi_turn_with_refusals_data.append(metadata_with_refusals)
                        else:
                            print(f"Skipping empty conversation: {file_path}")
                    
                    processed_count += 1
    
    # Create DataFrames
    single_turn_df = pd.DataFrame(single_turn_data)
    single_turn_with_refusals_df = pd.DataFrame(single_turn_with_refusals_data)
    multi_turn_df = pd.DataFrame(multi_turn_data)
    multi_turn_with_refusals_df = pd.DataFrame(multi_turn_with_refusals_data)
    
    print(f"Successfully processed {processed_count} files")
    print(f"Batch counts: {batch_counts}")
    print(f"Tactic counts: {tactic_counts}")
    print(f"Tactics included: {tactics_to_include}")
    print(f"Single-turn files: {len(single_turn_df)}")
    print(f"Single-turn entries (with refusals): {len(single_turn_with_refusals_df)}")
    print(f"Multi-turn files: {len(multi_turn_df)}")
    print(f"Multi-turn files (with refusals): {len(multi_turn_with_refusals_df)}")
    
    return {
        'single_turn': single_turn_df,
        'single_turn_with_refusals': single_turn_with_refusals_df,
        'multi_turn': multi_turn_df,
        'multi_turn_with_refusals': multi_turn_with_refusals_df
    }


def analyze_single_turn_by_samples(df: pd.DataFrame, max_samples: int = None, include_command: bool = False, extend_to_samples: int = None) -> pd.DataFrame:
    """
    Analyze single-turn data by number of samples using continuous StrongREJECT scores.
    Calculate expected maximum StrongREJECT score for s samples.
    Now supports multiple tactics, batches, and dynamic max_samples.
    """
    # Filter tactics if needed
    if not include_command:
        df = df[df['jailbreak_tactic'] == 'direct_request']
    
    # Check if batch column exists and include it in grouping
    group_cols = ['test_case', 'target_model', 'jailbreak_tactic']
    if 'batch' in df.columns:
        group_cols.append('batch')
    
    grouped = df.groupby(group_cols)
    
    results = []
    
    for group_key, group in grouped:
        # Get all scores for this combination
        scores = group['final_score'].tolist()
        n = len(scores)
        
        # Only process if we have enough samples
        if n >= 3:  # Minimum 3 samples
            result_row = {
                'test_case': group_key[0],
                'target_model': group_key[1],
                'jailbreak_tactic': group_key[2],
                'n_samples_available': n
            }
            
            # Add batch info if available
            if len(group_key) > 3:
                result_row['batch'] = group_key[3]
            
            # Determine the range to calculate and extend
            if max_samples is None:
                upper_limit = n
                extend_limit = extend_to_samples if extend_to_samples is not None else n
            else:
                upper_limit = min(n, max_samples)
                extend_limit = extend_to_samples if extend_to_samples is not None else max_samples
            
            # Calculate expected max scores for s = 1 to upper_limit
            calculated_scores = []
            for s in range(1, upper_limit + 1):
                expected_max = expected_max_formula(scores, s, n)
                calculated_scores.append(expected_max)
                result_row[f'expected_max_score_{s}_samples'] = expected_max
            
            # Extend with the last calculated score if needed
            if extend_limit > upper_limit and calculated_scores:
                last_score = calculated_scores[-1]
                for s in range(upper_limit + 1, extend_limit + 1):
                    result_row[f'expected_max_score_{s}_samples'] = last_score
            
            results.append(result_row)
    
    return pd.DataFrame(results)


def analyze_multi_turn_by_rounds(df: pd.DataFrame, max_rounds: int = None, include_command: bool = False, extend_to_rounds: int = None) -> pd.DataFrame:
    """
    Analyze multi-turn data by number of rounds using continuous StrongREJECT scores.
    For each conversation: calculate max score over first r rounds.
    Then average these max scores across conversations.
    Now supports multiple tactics, batches, and dynamic max_rounds.
    """
    # Filter tactics if needed
    if not include_command:
        df = df[df['jailbreak_tactic'] == 'direct_request']
    
    # Check if batch column exists and include it in grouping
    group_cols = ['test_case', 'target_model', 'jailbreak_tactic']
    if 'batch' in df.columns:
        group_cols.append('batch')
    
    grouped = df.groupby(group_cols)
    
    results = []
    
    for group_key, group in grouped:
        if len(group) > 0:
            result_row = {
                'test_case': group_key[0],
                'target_model': group_key[1],
                'jailbreak_tactic': group_key[2],
                'n_conversations': len(group)
            }
            
            # Add batch info if available
            if len(group_key) > 3:
                result_row['batch'] = group_key[3]
            
            # Determine the maximum number of rounds available in the data
            max_rounds_available = 0
            for _, conversation in group.iterrows():
                for col in conversation.index:
                    if 'max_score_by_' in col and '_rounds' in col:
                        try:
                            round_num = int(col.replace('max_score_by_', '').replace('_rounds', ''))
                            if not pd.isna(conversation[col]):
                                max_rounds_available = max(max_rounds_available, round_num)
                        except:
                            continue
            
            # Determine the range to calculate and extend
            if max_rounds is None:
                upper_limit = max_rounds_available
                extend_limit = extend_to_rounds if extend_to_rounds is not None else max_rounds_available
            else:
                upper_limit = max(max_rounds_available, max_rounds)  # Process all available data
                extend_limit = extend_to_rounds if extend_to_rounds is not None else max_rounds
            
            # Store calculated average scores for extension
            calculated_avg_scores = []
            
            # For each round r, calculate max over first r rounds per conversation, then average
            for r in range(1, upper_limit + 1):
                max_scores_for_round_r = []
                
                # For each conversation
                for _, conversation in group.iterrows():
                    # Get scores from rounds 1 to r for this conversation
                    scores_up_to_r = []
                    for round_num in range(1, r + 1):
                        score_col = f'max_score_by_{round_num}_rounds'
                        if score_col in conversation and not pd.isna(conversation[score_col]):
                            scores_up_to_r.append(conversation[score_col])
                    
                    # Calculate max score over first r rounds for this conversation
                    if scores_up_to_r:
                        max_score_up_to_r = max(scores_up_to_r)
                        max_scores_for_round_r.append(max_score_up_to_r)
                    else:
                        # If no data for this round, extend with previous max score
                        if calculated_avg_scores:
                            max_scores_for_round_r.append(calculated_avg_scores[-1])
                        else:
                            max_scores_for_round_r.append(0.0)
                
                # Average the max scores across all conversations
                if max_scores_for_round_r:
                    avg_max_score = sum(max_scores_for_round_r) / len(max_scores_for_round_r)
                    calculated_avg_scores.append(avg_max_score)
                    
                    # Only store if within requested range
                    if r <= extend_limit:
                        result_row[f'max_score_{r}_rounds'] = avg_max_score
                else:
                    calculated_avg_scores.append(0.0)
                    if r <= extend_limit:
                        result_row[f'max_score_{r}_rounds'] = 0.0
            
            # If we need more rounds than available data, extend with last calculated average
            if extend_limit > len(calculated_avg_scores) and calculated_avg_scores:
                last_avg_score = calculated_avg_scores[-1]
                for r in range(len(calculated_avg_scores) + 1, extend_limit + 1):
                    result_row[f'max_score_{r}_rounds'] = last_avg_score
            
            results.append(result_row)
    
    return pd.DataFrame(results)


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
    # Force LaTeX and font settings
    plt.rcParams.update({
        'text.usetex': True,
        'font.family': 'serif',
        'font.size': 24,
        'axes.labelsize': 24,
        'xtick.labelsize': 20,
        'ytick.labelsize': 20,
        'legend.fontsize': 18
    })
    # Get unique test cases (should be the same for both)
    test_cases = sorted(set(single_turn_results['test_case'].unique()) & 
                       set(multi_turn_results['test_case'].unique()))
    
    # Calculate subplot layout
    n_plots = len(test_cases)
    n_cols = min(3, n_plots)  # Max 3 columns
    n_rows = (n_plots + n_cols - 1) // n_cols  # Ceiling division
    
    # Create subplots with shared axes and no spacing
    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True, 
                            gridspec_kw={'hspace': 0, 'wspace': 0})
    
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

    # Track all legend elements for global legend
    global_legend_handles = []
    global_legend_labels = []
    labels_seen = set()

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
            
            # Group by batch if plotting multiple batches
            if batch_name_setting in ["both", "all"] and 'batch' in tactic_data.columns:
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
                        if batch_name_setting in ["both", "all"]:
                            label = f'{style["batch_label"]} (single)'
                        else:
                            label = f'{tactic} (single)'
                        
                        ax.scatter(samples, asr_scores, color=style['color'], s=50, alpha=0.7, 
                                  marker=style['marker'])
                        
                        # Add to global legend if not already seen
                        if label not in labels_seen:
                            labels_seen.add(label)
                            # Determine line style based on label content
                            if 'Claude' in label or 'batch6B' in label:
                                linestyle = '--'
                            elif 'Batch6C' in label or 'batch6C' in label:
                                linestyle = ':'
                            else:
                                linestyle = '-'
                            line_handle = plt.Line2D([0], [0], color=style['color'], linestyle=linestyle, linewidth=3)
                            global_legend_handles.append(line_handle)
                            global_legend_labels.append(label)
                        
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
            
            # Group by batch if plotting multiple batches
            if batch_name_setting in ["both", "all"] and 'batch' in tactic_data.columns:
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
                        if batch_name_setting in ["both", "all"]:
                            label = f'{style["batch_label"]} (multi)'
                        else:
                            label = f'{tactic} (multi)'
                        
                        ax.scatter(rounds, asr_scores, color=style['color'], s=50, alpha=0.7, 
                                  marker=style['marker'])
                        
                        # Add to global legend if not already seen
                        if label not in labels_seen:
                            labels_seen.add(label)
                            # Determine line style based on label content
                            if 'Claude' in label or 'batch6B' in label:
                                linestyle = '--'
                            elif 'Batch6C' in label or 'batch6C' in label:
                                linestyle = ':'
                            else:
                                linestyle = '-'
                            line_handle = plt.Line2D([0], [0], color=style['color'], linestyle=linestyle, linewidth=3)
                            global_legend_handles.append(line_handle)
                            global_legend_labels.append(label)
                        
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
        
        # Customize individual subplot with test case name as local legend
        ax.grid(True, alpha=0.3)
        
        # Add test case name as local legend in top-left corner
        test_case_formatted = test_case.replace('_', ' ').title()
        ax.text(0.05, 0.95, test_case_formatted, transform=ax.transAxes, 
                fontsize=14, verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Hide unused subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    # Global customization for shared axes
    fig.supxlabel(r'Number of Samples/Turns', fontsize=24, y=0.02)
    fig.supylabel(r'Score', fontsize=24, x=0.02)
    
    # Set shared axis properties
    for ax in axes[:n_plots]:
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.set_ylim(0, 1)
        if max_x > 0:
            ax.set_xticks(range(1, max_x + 1))
            ax.set_xlim(1, max_x)
    
    # Add global legend at bottom center
    if global_legend_handles:
        fig.legend(global_legend_handles, global_legend_labels, 
                  loc='lower center', bbox_to_anchor=(0.5, -0.05), 
                  ncol=len(global_legend_labels), fontsize=18)
    
    plt.tight_layout()
    
    # Adjust layout to make room for the bottom legend
    plt.subplots_adjust(bottom=0.15)

    if save_path:
        # Save as PDF
        pdf_path = save_path.replace('.png', '.pdf') if save_path.endswith('.png') else save_path + '.pdf'
        plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {pdf_path}")
    
    plt.show()


def plot_averaged_analysis(single_turn_results: pd.DataFrame, multi_turn_results: pd.DataFrame, 
                          batch_display_name: str, extend_xaxis: bool, include_command: bool,
                          batch_name_setting: str, title_suffix: str = "", figsize=(10, 6), save_path=None):
    """
    Plot averaged analysis across all test cases: single-turn ASR vs samples and multi-turn ASR vs rounds.
    Now supports multiple tactics, batches with different colors, error bars, and dynamic x-axis range.
    Fits are excluded from legend but printed to console.
    """
    # Force LaTeX and font settings
    plt.rcParams.update({
        'text.usetex': True,
        'font.family': 'serif',
        'font.size': 24,
        'axes.labelsize': 24,
        'xtick.labelsize': 20,
        'ytick.labelsize': 20,
        'legend.fontsize': 18
    })
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
        
        # Group by batch if plotting multiple batches
        if batch_name_setting in ["both", "all"] and 'batch' in tactic_data.columns:
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
                if batch_name_setting in ["both", "all"]:
                    label = f'{style["batch_label"]} (single)'
                else:
                    label = f'{tactic} (single)'
                
                # Plot data points without connecting lines
                ax.scatter(samples_range, single_turn_avg_scores, 
                          color=style['color'], marker=style['marker'], s=64, alpha=0.8,
                          label=label, zorder=5)
                
                # Add shaded region for standard deviation
                if single_turn_std_errors and len(single_turn_std_errors) > 0:
                    upper_bound = [avg + std for avg, std in zip(single_turn_avg_scores, single_turn_std_errors)]
                    lower_bound = [avg - std for avg, std in zip(single_turn_avg_scores, single_turn_std_errors)]
                    ax.fill_between(samples_range, lower_bound, upper_bound, 
                                   color=style['color'], alpha=0.2, zorder=1)
                
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
        
        # Group by batch if plotting multiple batches
        if batch_name_setting in ["both", "all"] and 'batch' in tactic_data.columns:
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
                if batch_name_setting in ["both", "all"]:
                    label = f'{style["batch_label"]} (multi)'
                else:
                    label = f'{tactic} (multi)'
                
                # Plot data points without connecting lines
                ax.scatter(rounds_range, multi_turn_avg_scores, 
                          color=style['color'], marker=style['marker'], s=64, alpha=0.8,
                          label=label, zorder=5)
                
                # Add shaded region for standard deviation
                if multi_turn_std_errors and len(multi_turn_std_errors) > 0:
                    upper_bound = [avg + std for avg, std in zip(multi_turn_avg_scores, multi_turn_std_errors)]
                    lower_bound = [avg - std for avg, std in zip(multi_turn_avg_scores, multi_turn_std_errors)]
                    ax.fill_between(rounds_range, lower_bound, upper_bound, 
                                   color=style['color'], alpha=0.2, zorder=1)
                
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
    
    # Customize the plot (no title)
    ax.set_xlabel(r'Number of Samples/Turns', fontsize=24)
    ax.set_ylabel(r'Average Score', fontsize=24)
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)  # StrongREJECT scores between 0 and 1
    
    # Set x-axis ticks and limits based on control variable
    if max_x > 0:
        ax.set_xticks(range(1, max_x + 1))
        ax.set_xlim(1, max_x)
    
    # Create custom legend with lines instead of points
    handles, labels = ax.get_legend_handles_labels()
    line_handles = []
    for handle, label in zip(handles, labels):
        # Get the style information from the handle
        color = handle.get_facecolor()[0] if hasattr(handle, 'get_facecolor') else handle.get_color()
        
        # Determine line style based on label content
        if 'Claude' in label or 'batch6B' in label:
            linestyle = '--'
        elif 'Batch6C' in label or 'batch6C' in label:
            linestyle = ':'
        else:
            linestyle = '-'
        
        # Create line handle
        line_handle = plt.Line2D([0], [0], color=color, linestyle=linestyle, linewidth=3)
        line_handles.append(line_handle)
    
    ax.legend(line_handles, labels, loc='center right', fontsize=18)
    
    plt.tight_layout()

    if save_path:
        # Save as PDF
        pdf_path = save_path.replace('.png', '.pdf') if save_path.endswith('.png') else save_path + '.pdf'
        plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {pdf_path}")
    
    plt.show()