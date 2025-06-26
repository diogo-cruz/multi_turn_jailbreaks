#!/usr/bin/env python3
"""
Corrected Score Histograms by Reasoning Token Bins - Batch Thinking + Direct Request
Creates histograms of maximum scores for different reasoning token bins
Properly computes scores as maximum over rounds per JSONL file
Separates single-turn and multi-turn data
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    print("Filtering for batch_thinking data and direct_request tactic only")
    print("Computing max score per JSONL file correctly")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Skip metadata line (first line)
            data_lines = lines[1:]
            
            # Collect data for this JSONL file
            conversation_scores = []
            conversation_reasoning_tokens = []
            metadata = {}
            is_direct_request = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Filter for direct_request tactic only
                    jailbreak_tactic = data.get('jailbreak_tactic', '').lower()
                    if jailbreak_tactic == 'direct_request':
                        is_direct_request = True
                    
                    # Extract score - treat scores not between 0 and 1 as 0
                    if data.get('score') is not None:
                        try:
                            score = float(data['score'])
                            if not (0 <= score <= 1):
                                score = 0
                            conversation_scores.append(score)
                        except (ValueError, TypeError):
                            conversation_scores.append(0)
                    
                    # Extract reasoning tokens
                    if 'token_usage' in data and data['token_usage'].get('reasoning_tokens'):
                        reasoning_tokens = data['token_usage']['reasoning_tokens']
                        if reasoning_tokens > 0:
                            conversation_reasoning_tokens.append(reasoning_tokens)
                    
                    # Extract other metadata
                    if not metadata:
                        metadata = {
                            'model': data.get('target_model', 'unknown'),
                            'test_case': data.get('test_case', 'unknown'),
                            'turn_type': data.get('turn_type', 'unknown'),
                            'reasoning_level': extract_reasoning_level(file_path.name, data)
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
            # Only include conversations with direct_request tactic and scores
            if is_direct_request and conversation_scores:
                # CORRECT SCORE COMPUTATION: Maximum score across all rounds
                max_score = max(conversation_scores)
                
                # Average reasoning tokens (only counting non-zero tokens)
                avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
                
                conversation_record = {
                    'file': file_path.name,
                    'max_score': max_score,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'num_rounds': len(conversation_scores),
                    **metadata
                }
                
                # Separate by turn type
                if metadata.get('turn_type') == 'single_turn':
                    single_turn_data.append(conversation_record)
                elif metadata.get('turn_type') == 'multi_turn':
                    multi_turn_data.append(conversation_record)
                else:
                    # Infer from filename
                    if 'single_turn' in file_path.name:
                        single_turn_data.append(conversation_record)
                    elif 'multi_turn' in file_path.name:
                        multi_turn_data.append(conversation_record)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    print(f"Loaded {len(single_turn_data)} single-turn conversations")
    print(f"Loaded {len(multi_turn_data)} multi-turn conversations")
    
    return pd.DataFrame(single_turn_data), pd.DataFrame(multi_turn_data)

def extract_reasoning_level(filename, data):
    """Extract reasoning level from filename or data"""
    if 'reasoning_high' in filename:
        return 'high'
    elif 'reasoning_medium' in filename:
        return 'medium'
    elif 'reasoning_low' in filename:
        return 'low'
    elif 'reasoning_none' in filename:
        return 'none'
    return 'unknown'

def analyze_score_computation(df, turn_type):
    """Analyze how scores are distributed"""
    
    print(f"\n=== {turn_type.upper()} SCORE ANALYSIS ===")
    
    if len(df) == 0:
        print("No data available")
        return
    
    # Look at unique values of score
    unique_scores = sorted(df['max_score'].unique())
    print(f"Unique max score values: {unique_scores}")
    
    # Count frequency of each score
    score_counts = df['max_score'].value_counts().sort_index()
    print(f"\nScore frequency distribution:")
    for score, count in score_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  Score {score}: {count} occurrences ({percentage:.1f}%)")
    
    print(f"Mean max score: {df['max_score'].mean():.3f}")
    print(f"Success rate (score = 1.0): {(df['max_score'] >= 1.0).mean() * 100:.1f}%")

def create_reasoning_token_bins(df, turn_type):
    """Create reasoning token bins and analyze score distributions"""
    
    if len(df) == 0:
        return df, []
    
    print(f"\n=== {turn_type.upper()} TOKEN BINS ===")
    
    # Define bins
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Create bins
    df['reasoning_bin'] = pd.cut(df['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Print bin statistics
    for label in bin_labels:
        bin_data = df[df['reasoning_bin'] == label]
        if len(bin_data) > 0:
            avg_score = bin_data['max_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            count = len(bin_data)
            print(f"{label}: avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, n={count}")
    
    return df, bin_labels

def create_score_histograms(single_df, multi_df, single_bins, multi_bins):
    """Create histograms of maximum scores for each reasoning token bin"""
    
    print("\nGenerating corrected score histograms...")
    
    # Create figure with subplots - 2 rows (single/multi), 6 columns (5 bins + overall)
    fig, axes = plt.subplots(2, 6, figsize=(24, 12))
    
    # Define colors for each bin
    colors = ['red', 'orange', 'gold', 'lightgreen', 'darkgreen']
    
    # Single-turn histograms (top row)
    if len(single_df) > 0:
        # Plot histogram for each bin
        for i, (label, color) in enumerate(zip(single_bins, colors)):
            ax = axes[0, i]
            bin_data = single_df[single_df['reasoning_bin'] == label]
            
            if len(bin_data) > 0:
                scores = bin_data['max_score']
                
                # Create histogram
                ax.hist(scores, bins=np.arange(0, 1.125, 0.125), alpha=0.7, color=color, edgecolor='black', density=True)
                ax.set_xlabel('Maximum Score')
                ax.set_ylabel('Density')
                ax.set_title(f'Single-Turn: {label} Tokens\n(n={len(bin_data)})')
                ax.set_xlim(0, 1)
                ax.grid(True, alpha=0.3)
                
                # Add statistics
                mean_score = scores.mean()
                success_rate = (scores >= 1.0).mean() * 100
                ax.axvline(mean_score, color='blue', linestyle='--', alpha=0.8, linewidth=2)
                ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
                       transform=ax.transAxes, verticalalignment='top', 
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                       horizontalalignment='center', verticalalignment='center')
                ax.set_title(f'Single-Turn: {label} Tokens\n(n=0)')
        
        # Overall single-turn distribution
        ax = axes[0, 5]
        all_scores = single_df['max_score']
        ax.hist(all_scores, bins=np.arange(0, 1.125, 0.125), alpha=0.7, color='blue', edgecolor='black', density=True)
        ax.set_xlabel('Maximum Score')
        ax.set_ylabel('Density')
        ax.set_title(f'Single-Turn: Overall\n(n={len(single_df)})')
        ax.set_xlim(0, 1)
        ax.grid(True, alpha=0.3)
        
        # Add overall statistics
        mean_score = all_scores.mean()
        success_rate = (all_scores >= 1.0).mean() * 100
        ax.axvline(mean_score, color='red', linestyle='--', alpha=0.8, linewidth=2)
        ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
               transform=ax.transAxes, verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Multi-turn histograms (bottom row)
    if len(multi_df) > 0:
        # Plot histogram for each bin
        for i, (label, color) in enumerate(zip(multi_bins, colors)):
            ax = axes[1, i]
            bin_data = multi_df[multi_df['reasoning_bin'] == label]
            
            if len(bin_data) > 0:
                scores = bin_data['max_score']
                
                # Create histogram
                ax.hist(scores, bins=np.arange(0, 1.125, 0.125), alpha=0.7, color=color, edgecolor='black', density=True)
                ax.set_xlabel('Maximum Score')
                ax.set_ylabel('Density')
                ax.set_title(f'Multi-Turn: {label} Tokens\n(n={len(bin_data)})')
                ax.set_xlim(0, 1)
                ax.grid(True, alpha=0.3)
                
                # Add statistics
                mean_score = scores.mean()
                success_rate = (scores >= 1.0).mean() * 100
                ax.axvline(mean_score, color='blue', linestyle='--', alpha=0.8, linewidth=2)
                ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
                       transform=ax.transAxes, verticalalignment='top', 
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            else:
                ax.text(0.5, 0.5, 'No Data', transform=ax.transAxes, 
                       horizontalalignment='center', verticalalignment='center')
                ax.set_title(f'Multi-Turn: {label} Tokens\n(n=0)')
        
        # Overall multi-turn distribution
        ax = axes[1, 5]
        all_scores = multi_df['max_score']
        ax.hist(all_scores, bins=np.arange(0, 1.125, 0.125), alpha=0.7, color='green', edgecolor='black', density=True)
        ax.set_xlabel('Maximum Score')
        ax.set_ylabel('Density')
        ax.set_title(f'Multi-Turn: Overall\n(n={len(multi_df)})')
        ax.set_xlim(0, 1)
        ax.grid(True, alpha=0.3)
        
        # Add overall statistics
        mean_score = all_scores.mean()
        success_rate = (all_scores >= 1.0).mean() * 100
        ax.axvline(mean_score, color='red', linestyle='--', alpha=0.8, linewidth=2)
        ax.text(0.05, 0.95, f'Mean: {mean_score:.3f}\nSuccess: {success_rate:.1f}%', 
               transform=ax.transAxes, verticalalignment='top', 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('corrected_score_histograms.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main analysis function"""
    
    print("Starting Corrected Score Histogram Analysis...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Analyze score computation
    analyze_score_computation(single_df, "single-turn")
    analyze_score_computation(multi_df, "multi-turn")
    
    # Create reasoning token bins
    single_df, single_bins = create_reasoning_token_bins(single_df, "single-turn")
    multi_df, multi_bins = create_reasoning_token_bins(multi_df, "multi-turn")
    
    # Create histograms
    create_score_histograms(single_df, multi_df, single_bins, multi_bins)
    
    print("\nCorrected analysis complete! Histograms saved as 'corrected_score_histograms.png'")

if __name__ == "__main__":
    main()