#!/usr/bin/env python3
"""
Corrected Model Comparison Analysis - Batch Thinking + Direct Request
Plots score vs reasoning tokens (in bins) for single and multi-turn, separately for each model
Properly computes scores as maximum over rounds per JSONL file
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import math

def clean_model_name(raw_model_name):
    """Clean up model names for display"""
    if not raw_model_name or raw_model_name == 'unknown':
        return 'unknown'
    
    # Remove provider prefixes and extract main model name
    model_name = raw_model_name.lower()
    
    if 'claude' in model_name:
        return 'Claude'
    elif 'gemini' in model_name:
        return 'Gemini'
    elif 'gpt' in model_name or 'o1-mini' in model_name or 'o3-mini' in model_name or 'o4-mini' in model_name:
        return 'OpenAI'
    elif 'qwen' in model_name:
        return 'Qwen'
    else:
        # Return the part after the slash if it exists, otherwise the whole name
        if '/' in raw_model_name:
            return raw_model_name.split('/')[-1].title()
        return raw_model_name.title()

def load_and_process_data(data_dir="../clean_results/final_runs/batch_thinking"):
    """Load data and compute scores correctly"""
    data_dir = Path(data_dir)
    single_turn_data = []
    multi_turn_data = []
    
    print("Loading data from", data_dir)
    print("Processing batch_thinking data from both direct_request and command tactics")
    print("Extracting model names from metadata line and cleaning for display")
    print("Computing max score per JSONL file correctly")
    
    # Find all JSONL files recursively
    jsonl_files = list(data_dir.glob("**/*.jsonl"))
    print("Found", len(jsonl_files), "JSONL files")
    
    for file_path in jsonl_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                continue
                
            # Extract metadata from first line
            try:
                metadata_line = json.loads(lines[0].strip())
                file_metadata = {
                    'model': clean_model_name(metadata_line.get('target_model', 'unknown')),
                    'test_case': metadata_line.get('test_case', 'unknown'),
                    'turn_type': metadata_line.get('turn_type', 'unknown'),
                    'jailbreak_tactic': metadata_line.get('jailbreak_tactic', 'unknown'),
                    'reasoning_level': extract_reasoning_level(file_path.name, metadata_line)
                }
            except json.JSONDecodeError as e:
                print(f"Error parsing metadata in {file_path}: {e}")
                continue
                
            # Process data lines (skip metadata line)
            data_lines = lines[1:]
            
            # Collect data for this JSONL file
            conversation_scores = []
            conversation_reasoning_tokens = []
            valid_data_found = False
            
            for line_num, line in enumerate(data_lines, 2):
                try:
                    data = json.loads(line.strip())
                    
                    # Only process if this matches our target tactics
                    jailbreak_tactic = data.get('jailbreak_tactic', file_metadata['jailbreak_tactic']).lower()
                    if jailbreak_tactic in ['direct_request', 'command']:
                        valid_data_found = True
                    
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
                        
                except json.JSONDecodeError as e:
                    print(f"JSON error in {file_path}:{line_num} - {e}")
                    continue
                except Exception as e:
                    print(f"Error processing {file_path}:{line_num} - {e}")
                    continue
                    
            # Only include conversations with valid tactic and scores
            if valid_data_found and conversation_scores:
                # CORRECT SCORE COMPUTATION: Maximum score across all rounds
                max_score = max(conversation_scores)
                
                # Average reasoning tokens (only counting non-zero tokens)
                avg_reasoning_tokens = np.mean(conversation_reasoning_tokens) if conversation_reasoning_tokens else 0
                
                conversation_record = {
                    'file': file_path.name,
                    'max_score': max_score,
                    'avg_reasoning_tokens': avg_reasoning_tokens,
                    'num_rounds': len(conversation_scores),
                    **file_metadata
                }
                
                # Separate by turn type
                turn_type = file_metadata.get('turn_type', 'unknown')
                if turn_type == 'single' or 'single_turn' in file_path.name:
                    single_turn_data.append(conversation_record)
                elif turn_type == 'multi' or 'multi_turn' in file_path.name:
                    multi_turn_data.append(conversation_record)
                else:
                    print(f"Unknown turn type '{turn_type}' in {file_path.name}")
                    
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

def analyze_models(df, turn_type):
    """Analyze model distribution and sample sizes"""
    
    print(f"\n=== {turn_type.upper()} MODEL ANALYSIS ===")
    
    if len(df) == 0:
        print("No data available")
        return []
    
    # Get model distribution
    model_counts = df['model'].value_counts()
    print(f"Total conversations: {len(df)}")
    print(f"Unique models: {len(model_counts)}")
    print("\nModel distribution:")
    
    models_with_sufficient_data = []
    for model, count in model_counts.items():
        print(f"  {model}: {count} conversations")
        if count >= 10:  # Minimum threshold for analysis
            models_with_sufficient_data.append(model)
    
    print(f"\nModels with sufficient data (≥10 conversations): {len(models_with_sufficient_data)}")
    for model in models_with_sufficient_data:
        model_data = df[df['model'] == model]
        avg_score = model_data['max_score'].mean()
        success_rate = (model_data['max_score'] >= 1.0).mean() * 100
        avg_tokens = model_data['avg_reasoning_tokens'].mean()
        correlation = model_data['avg_reasoning_tokens'].corr(model_data['max_score'])
        print(f"  {model}: avg_score={avg_score:.3f}, success_rate={success_rate:.1f}%, "
              f"avg_tokens={avg_tokens:.0f}, correlation={correlation:.3f}")
    
    return models_with_sufficient_data

def create_reasoning_token_bins(df, model, turn_type):
    """Create reasoning token bins for a specific model"""
    
    model_data = df[df['model'] == model].copy()
    
    if len(model_data) == 0:
        return model_data, []
    
    # Define bins
    bin_edges = [0, 200, 500, 1000, 2000, float('inf')]
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Create bins
    model_data['reasoning_bin'] = pd.cut(model_data['avg_reasoning_tokens'], bins=bin_edges, labels=bin_labels, right=False)
    
    # Calculate bin statistics
    bin_stats = []
    for label in bin_labels:
        bin_data = model_data[model_data['reasoning_bin'] == label]
        if len(bin_data) > 0:
            avg_score = bin_data['max_score'].mean()
            success_rate = (bin_data['max_score'] >= 1.0).mean() * 100
            count = len(bin_data)
            avg_tokens = bin_data['avg_reasoning_tokens'].mean()
            bin_stats.append({
                'bin': label,
                'avg_score': avg_score,
                'success_rate': success_rate,
                'count': count,
                'avg_tokens': avg_tokens
            })
        else:
            bin_stats.append({
                'bin': label,
                'avg_score': 0,
                'success_rate': 0,
                'count': 0,
                'avg_tokens': 0
            })
    
    return model_data, bin_stats

def create_model_comparison_plots(single_df, multi_df, single_models, multi_models):
    """Create comprehensive model comparison plots"""
    
    print("\nGenerating model comparison plots...")
    
    # Determine the layout based on number of models
    max_models = max(len(single_models), len(multi_models))
    
    if max_models == 0:
        print("No models with sufficient data found")
        return
    
    # Calculate grid dimensions
    cols = min(4, max_models)  # Maximum 4 columns
    rows = math.ceil(max_models / cols) * 2  # 2 rows per model comparison (single + multi)
    
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    
    # Ensure axes is always 2D
    if rows == 1:
        axes = axes.reshape(1, -1)
    if cols == 1:
        axes = axes.reshape(-1, 1)
    
    # Color scheme for bins
    bin_colors = ['red', 'orange', 'gold', 'lightgreen', 'darkgreen']
    bin_labels = ['0-200', '200-500', '500-1000', '1000-2000', '2000+']
    
    # Plot single-turn models (top half)
    for i, model in enumerate(single_models):
        if i >= cols:
            break
            
        row = i // cols * 2  # Single-turn in even rows
        col = i % cols
        ax = axes[row, col] if rows > 1 else axes[col]
        
        model_data, bin_stats = create_reasoning_token_bins(single_df, model, "single-turn")
        
        if bin_stats:
            bins = [stat['bin'] for stat in bin_stats if stat['count'] > 0]
            scores = [stat['avg_score'] for stat in bin_stats if stat['count'] > 0]
            counts = [stat['count'] for stat in bin_stats if stat['count'] > 0]
            colors = [bin_colors[j] for j, stat in enumerate(bin_stats) if stat['count'] > 0]
            
            if bins and scores:
                bars = ax.bar(bins, scores, color=colors, alpha=0.8, edgecolor='black')
                
                # Add value labels
                for bar, score, count in zip(bars, scores, counts):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                           f'{score:.3f}\n(n={count})', ha='center', va='bottom', fontsize=8)
                
                ax.set_ylim(0, 1)
                ax.set_ylabel('Average Max Score')
                ax.set_title(f'Single-Turn: {model}\n(Total: {len(model_data)} conversations)')
                ax.grid(True, alpha=0.3)
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'No Data\nwith Reasoning', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Single-Turn: {model}\n(No reasoning data)')
        else:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Single-Turn: {model}\n(No data)')
    
    # Plot multi-turn models (bottom half)
    for i, model in enumerate(multi_models):
        if i >= cols:
            break
            
        row = i // cols * 2 + 1  # Multi-turn in odd rows
        col = i % cols
        ax = axes[row, col] if rows > 1 else axes[col]
        
        model_data, bin_stats = create_reasoning_token_bins(multi_df, model, "multi-turn")
        
        if bin_stats:
            bins = [stat['bin'] for stat in bin_stats if stat['count'] > 0]
            scores = [stat['avg_score'] for stat in bin_stats if stat['count'] > 0]
            counts = [stat['count'] for stat in bin_stats if stat['count'] > 0]
            colors = [bin_colors[j] for j, stat in enumerate(bin_stats) if stat['count'] > 0]
            
            if bins and scores:
                bars = ax.bar(bins, scores, color=colors, alpha=0.8, edgecolor='black')
                
                # Add value labels
                for bar, score, count in zip(bars, scores, counts):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                           f'{score:.3f}\n(n={count})', ha='center', va='bottom', fontsize=8)
                
                ax.set_ylim(0, 1)
                ax.set_ylabel('Average Max Score')
                ax.set_title(f'Multi-Turn: {model}\n(Total: {len(model_data)} conversations)')
                ax.grid(True, alpha=0.3)
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'No Data\nwith Reasoning', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Multi-Turn: {model}\n(No reasoning data)')
        else:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Multi-Turn: {model}\n(No data)')
    
    # Fill remaining subplots
    total_plots = len(single_models) + len(multi_models)
    for i in range(total_plots, rows * cols):
        row = i // cols
        col = i % cols
        ax = axes[row, col] if rows > 1 else axes[col]
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('corrected_model_comparison_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_model_summary_plots(single_df, multi_df, single_models, multi_models):
    """Create summary comparison plots across models"""
    
    print("\nGenerating model summary plots...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Average scores by model (single-turn)
    ax = axes[0, 0]
    if single_models:
        model_scores = []
        model_names = []
        for model in single_models:
            model_data = single_df[single_df['model'] == model]
            avg_score = model_data['max_score'].mean()
            model_scores.append(avg_score)
            model_names.append(model.split('-')[0] if '-' in model else model)  # Shorten names
        
        bars = ax.bar(range(len(model_names)), model_scores, color='blue', alpha=0.7)
        ax.set_ylabel('Average Max Score')
        ax.set_title('Single-Turn: Average Score by Model')
        ax.set_xticks(range(len(model_names)))
        ax.set_xticklabels(model_names, rotation=45, ha='right')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, score in zip(bars, model_scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                   f'{score:.3f}', ha='center', va='bottom', fontsize=10)
    else:
        ax.text(0.5, 0.5, 'No Single-Turn\nModels', ha='center', va='center', transform=ax.transAxes)
    
    # 2. Average scores by model (multi-turn)
    ax = axes[0, 1]
    if multi_models:
        model_scores = []
        model_names = []
        for model in multi_models:
            model_data = multi_df[multi_df['model'] == model]
            avg_score = model_data['max_score'].mean()
            model_scores.append(avg_score)
            model_names.append(model.split('-')[0] if '-' in model else model)  # Shorten names
        
        bars = ax.bar(range(len(model_names)), model_scores, color='green', alpha=0.7)
        ax.set_ylabel('Average Max Score')
        ax.set_title('Multi-Turn: Average Score by Model')
        ax.set_xticks(range(len(model_names)))
        ax.set_xticklabels(model_names, rotation=45, ha='right')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, score in zip(bars, model_scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                   f'{score:.3f}', ha='center', va='bottom', fontsize=10)
    else:
        ax.text(0.5, 0.5, 'No Multi-Turn\nModels', ha='center', va='center', transform=ax.transAxes)
    
    # 3. Success rates by model comparison
    ax = axes[0, 2]
    common_models = set(single_models) & set(multi_models)
    if common_models:
        common_models = list(common_models)
        single_success = []
        multi_success = []
        
        for model in common_models:
            single_model_data = single_df[single_df['model'] == model]
            multi_model_data = multi_df[multi_df['model'] == model]
            
            single_success.append((single_model_data['max_score'] >= 1.0).mean() * 100)
            multi_success.append((multi_model_data['max_score'] >= 1.0).mean() * 100)
        
        x = np.arange(len(common_models))
        width = 0.35
        
        ax.bar(x - width/2, single_success, width, label='Single-Turn', color='blue', alpha=0.7)
        ax.bar(x + width/2, multi_success, width, label='Multi-Turn', color='green', alpha=0.7)
        
        ax.set_ylabel('Success Rate (%)')
        ax.set_title('Success Rate Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([model.split('-')[0] for model in common_models], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No Common\nModels', ha='center', va='center', transform=ax.transAxes)
    
    # 4. Correlation comparison
    ax = axes[1, 0]
    if single_models:
        correlations = []
        model_names = []
        for model in single_models:
            model_data = single_df[single_df['model'] == model]
            if len(model_data) > 5:  # Need minimum data for correlation
                corr = model_data['avg_reasoning_tokens'].corr(model_data['max_score'])
                if not np.isnan(corr):
                    correlations.append(corr)
                    model_names.append(model.split('-')[0])
        
        if correlations:
            bars = ax.bar(range(len(model_names)), correlations, color='blue', alpha=0.7)
            ax.set_ylabel('Correlation (Tokens vs Score)')
            ax.set_title('Single-Turn: Reasoning-Score Correlation')
            ax.set_xticks(range(len(model_names)))
            ax.set_xticklabels(model_names, rotation=45, ha='right')
            ax.set_ylim(-1, 1)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, corr in zip(bars, correlations):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                       f'{corr:.3f}', ha='center', va='bottom', fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Insufficient Data\nfor Correlations', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No Single-Turn\nModels', ha='center', va='center', transform=ax.transAxes)
    
    # 5. Multi-turn correlation
    ax = axes[1, 1]
    if multi_models:
        correlations = []
        model_names = []
        for model in multi_models:
            model_data = multi_df[multi_df['model'] == model]
            if len(model_data) > 5:  # Need minimum data for correlation
                corr = model_data['avg_reasoning_tokens'].corr(model_data['max_score'])
                if not np.isnan(corr):
                    correlations.append(corr)
                    model_names.append(model.split('-')[0])
        
        if correlations:
            bars = ax.bar(range(len(model_names)), correlations, color='green', alpha=0.7)
            ax.set_ylabel('Correlation (Tokens vs Score)')
            ax.set_title('Multi-Turn: Reasoning-Score Correlation')
            ax.set_xticks(range(len(model_names)))
            ax.set_xticklabels(model_names, rotation=45, ha='right')
            ax.set_ylim(-1, 1)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.grid(True, alpha=0.3)
            
            # Add value labels
            for bar, corr in zip(bars, correlations):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                       f'{corr:.3f}', ha='center', va='bottom', fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Insufficient Data\nfor Correlations', ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, 'No Multi-Turn\nModels', ha='center', va='center', transform=ax.transAxes)
    
    # 6. Sample size comparison
    ax = axes[1, 2]
    all_models = list(set(single_models + multi_models))
    if all_models:
        model_names = []
        single_counts = []
        multi_counts = []
        
        for model in all_models:
            single_count = len(single_df[single_df['model'] == model]) if model in single_models else 0
            multi_count = len(multi_df[multi_df['model'] == model]) if model in multi_models else 0
            
            model_names.append(model.split('-')[0])
            single_counts.append(single_count)
            multi_counts.append(multi_count)
        
        x = np.arange(len(model_names))
        width = 0.35
        
        ax.bar(x - width/2, single_counts, width, label='Single-Turn', color='blue', alpha=0.7)
        ax.bar(x + width/2, multi_counts, width, label='Multi-Turn', color='green', alpha=0.7)
        
        ax.set_ylabel('Number of Conversations')
        ax.set_title('Sample Size by Model')
        ax.set_xticks(x)
        ax.set_xticklabels(model_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No Models\nFound', ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    plt.savefig('corrected_model_summary_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_model_analysis_report(single_df, multi_df, single_models, multi_models):
    """Generate comprehensive model analysis report"""
    
    report = f"""
# Model Comparison Analysis Report - Batch Thinking + Direct Request

## Dataset Overview
- **Single-Turn Models with Sufficient Data (≥10 conversations)**: {len(single_models)}
- **Multi-Turn Models with Sufficient Data (≥10 conversations)**: {len(multi_models)}
- **Total Single-Turn Conversations**: {len(single_df):,}
- **Total Multi-Turn Conversations**: {len(multi_df):,}

## Model Performance Analysis

### Single-Turn Models
"""
    
    if single_models:
        for model in single_models:
            model_data = single_df[single_df['model'] == model]
            avg_score = model_data['max_score'].mean()
            success_rate = (model_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = model_data['avg_reasoning_tokens'].mean()
            correlation = model_data['avg_reasoning_tokens'].corr(model_data['max_score'])
            
            report += f"""
**{model}** (n={len(model_data)}):
- Average max score: {avg_score:.3f}
- Success rate: {success_rate:.1f}%
- Average reasoning tokens: {avg_tokens:.0f}
- Correlation (tokens vs score): {correlation:.3f}
"""
    else:
        report += "- No single-turn models with sufficient data\n"
    
    report += f"""
### Multi-Turn Models
"""
    
    if multi_models:
        for model in multi_models:
            model_data = multi_df[multi_df['model'] == model]
            avg_score = model_data['max_score'].mean()
            success_rate = (model_data['max_score'] >= 1.0).mean() * 100
            avg_tokens = model_data['avg_reasoning_tokens'].mean()
            correlation = model_data['avg_reasoning_tokens'].corr(model_data['max_score'])
            
            report += f"""
**{model}** (n={len(model_data)}):
- Average max score: {avg_score:.3f}
- Success rate: {success_rate:.1f}%
- Average reasoning tokens: {avg_tokens:.0f}
- Correlation (tokens vs score): {correlation:.3f}
"""
    else:
        report += "- No multi-turn models with sufficient data\n"
    
    # Compare common models
    common_models = set(single_models) & set(multi_models)
    if common_models:
        report += f"""
### Multi-Turn vs Single-Turn Comparison (Common Models)
"""
        
        for model in common_models:
            single_data = single_df[single_df['model'] == model]
            multi_data = multi_df[multi_df['model'] == model]
            
            single_score = single_data['max_score'].mean()
            multi_score = multi_data['max_score'].mean()
            score_diff = multi_score - single_score
            
            single_success = (single_data['max_score'] >= 1.0).mean() * 100
            multi_success = (multi_data['max_score'] >= 1.0).mean() * 100
            success_diff = multi_success - single_success
            
            report += f"""
**{model}**:
- Score improvement (multi vs single): {score_diff:+.3f}
- Success rate improvement: {success_diff:+.1f}%
"""
    
    return report

def main():
    """Main analysis function"""
    
    print("Starting Corrected Model Comparison Analysis...")
    
    # Load data
    single_df, multi_df = load_and_process_data()
    
    # Analyze models
    single_models = analyze_models(single_df, "single-turn")
    multi_models = analyze_models(multi_df, "multi-turn")
    
    if not single_models and not multi_models:
        print("No models with sufficient data found!")
        return
    
    # Create model comparison plots
    create_model_comparison_plots(single_df, multi_df, single_models, multi_models)
    
    # Create summary plots
    create_model_summary_plots(single_df, multi_df, single_models, multi_models)
    
    # Generate report
    report = generate_model_analysis_report(single_df, multi_df, single_models, multi_models)
    
    # Save report
    with open('corrected_model_analysis_report.md', 'w') as f:
        f.write(report)
    
    print(f"\nModel comparison analysis complete!")
    print(f"- Main visualization saved as 'corrected_model_comparison_analysis.png'")
    print(f"- Summary visualization saved as 'corrected_model_summary_analysis.png'")
    print(f"- Report saved as 'corrected_model_analysis_report.md'")
    print(report)

if __name__ == "__main__":
    main()