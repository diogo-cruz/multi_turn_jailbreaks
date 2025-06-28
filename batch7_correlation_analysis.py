import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import ast
import matplotlib.patches as patches

# Use LaTeX font
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern']

def parse_scores(score_str, turn_type):
    """Parse the scores string and return appropriate score based on turn type"""
    try:
        if pd.isna(score_str) or score_str == '[]':
            return np.nan
        scores = ast.literal_eval(score_str)
        if not scores:
            return np.nan
        
        if turn_type == 'single':
            return scores[0]  # Single turn: use the only score
        else:  # multi-turn
            return max(scores)  # Multi-turn: use maximum score across all turns
    except:
        return np.nan

def load_and_process_data():
    """Load and process the batch7 data"""
    df = pd.read_csv('/home/dcruz/multi_turn_jailbreaks/csv_results/master_results_with_fp.csv')
    
    # Filter for batch7 and direct_request jailbreak tactic
    batch7_df = df[df['batch'] == 'batch7'].copy()
    batch7_df = batch7_df[batch7_df['jailbreak_tactic'] == 'direct_request'].copy()
    
    # Parse scores based on turn type (final for single, max for multi)
    batch7_df['analysis_score'] = batch7_df.apply(
        lambda row: parse_scores(row['scores'], row['turn_type']), axis=1
    )
    
    # Remove rows with NaN scores
    batch7_df = batch7_df.dropna(subset=['analysis_score'])
    
    return batch7_df

def create_correlation_matrix(df, turn_type):
    """Create correlation matrix for specified turn type"""
    # Filter by turn type
    turn_df = df[df['turn_type'] == turn_type].copy()
    
    # Pivot data to have models as columns and test cases as rows
    pivot_df = turn_df.pivot_table(
        index='test_case', 
        columns='target_model', 
        values='analysis_score', 
        aggfunc='mean'  # In case there are multiple runs
    )
    
    # Map API names to common names
    api_to_common = {
        'anthropic/claude-3-sonnet': 'Claude 3 Sonnet',
        'anthropic/claude-3.5-sonnet': 'Claude 3.5 Sonnet',
        'anthropic/claude-3.7-sonnet': 'Claude 3.7 Sonnet',
        'anthropic/claude-sonnet-4': 'Claude Sonnet 4',
        'openai/gpt-4o-2024-05-13': 'GPT-4o (old)',
        'openai/gpt-4o': 'GPT-4o',
        'openai/gpt-4.1': 'GPT-4.1',
        'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
        'openai/gpt-4.1-nano': 'GPT-4.1 Nano',
        'google/gemini-2.5-flash': 'Gemini 2.5 Flash',
        'google/gemini-2.5-flash-lite-preview-06-17': 'Gemini 2.5 Flash Lite',
        'google/gemini-2.5-pro': 'Gemini 2.5 Pro'
    }
    
    # Rename columns to common names
    pivot_df.columns = [api_to_common.get(col, col) for col in pivot_df.columns]
    
    # Define desired order: Claude family (by age), GPT family (by age), Gemini family
    desired_order = [
        'Claude 3 Sonnet',
        'Claude 3.5 Sonnet', 
        'Claude 3.7 Sonnet',
        'Claude Sonnet 4',
        'GPT-4o (old)',
        'GPT-4o',
        'GPT-4.1',
        'GPT-4.1 Mini',
        'GPT-4.1 Nano',
        'Gemini 2.5 Flash',
        'Gemini 2.5 Flash Lite',
        'Gemini 2.5 Pro'
    ]
    
    # Reorder columns and rows according to desired order
    available_models = [model for model in desired_order if model in pivot_df.columns]
    pivot_df = pivot_df[available_models]
    
    # Calculate correlation matrix
    corr_matrix = pivot_df.corr()
    
    # Reorder correlation matrix rows to match column order
    corr_matrix = corr_matrix.reindex(available_models)
    
    return corr_matrix, pivot_df

def plot_correlation_matrix(corr_matrix, turn_type, save_path):
    """Plot and save correlation matrix"""
    plt.figure(figsize=(14, 12))
    
    # Create heatmap
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Mask upper triangle
    heatmap = sns.heatmap(
        corr_matrix, 
        annot=True, 
        cmap='RdBu_r', 
        center=0,
        mask=mask,
        square=True,
        fmt='.3f',
        cbar_kws={'shrink': 0.8},
        linewidths=0.5,
        linecolor='black',
        annot_kws={'fontsize': 14}
    )
    
    # Set font size to 20px for axis labels
    plt.xticks(fontsize=20, rotation=45, ha='right')
    plt.yticks(fontsize=20, rotation=0)
    
    # Remove title, x and y labels as requested
    plt.xlabel('')
    plt.ylabel('')
    
    # Add thicker borders for same-lab comparisons
    def get_lab(model_name):
        if 'Claude' in model_name:
            return 'Anthropic'
        elif 'GPT' in model_name:
            return 'OpenAI'
        elif 'Gemini' in model_name:
            return 'Google'
        return 'Unknown'
    
    # Get the axis object
    ax = plt.gca()
    
    # Add thick borders for same-lab pairs
    models = corr_matrix.columns.tolist()
    n_models = len(models)
    
    for i in range(n_models):
        for j in range(n_models):
            # Only process lower triangle (where data is shown)
            if j >= i:
                continue
                
            model_i = models[i]
            model_j = models[j]
            
            if get_lab(model_i) == get_lab(model_j):
                # Add thick border for same lab - coordinates are (j, i) for lower triangle
                rect = patches.Rectangle((j, i), 1, 1, linewidth=3, 
                                       edgecolor='black', facecolor='none')
                ax.add_patch(rect)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    return heatmap

def print_summary_stats(corr_matrix, pivot_df, turn_type):
    """Print summary statistics"""
    print(f"\n=== {turn_type.upper()}-TURN ANALYSIS ===")
    print(f"Number of models: {len(corr_matrix.columns)}")
    print(f"Number of test cases: {len(pivot_df.index)}")
    print(f"Models analyzed: {', '.join(corr_matrix.columns)}")
    
    # Get correlation values (excluding diagonal)
    corr_values = corr_matrix.values
    mask = ~np.eye(corr_values.shape[0], dtype=bool)
    off_diagonal_corrs = corr_values[mask]
    
    print(f"\nCorrelation Statistics:")
    print(f"Mean correlation: {np.mean(off_diagonal_corrs):.3f}")
    print(f"Median correlation: {np.median(off_diagonal_corrs):.3f}")
    print(f"Min correlation: {np.min(off_diagonal_corrs):.3f}")
    print(f"Max correlation: {np.max(off_diagonal_corrs):.3f}")
    print(f"Std correlation: {np.std(off_diagonal_corrs):.3f}")
    
    # Find highest and lowest correlations
    corr_matrix_masked = corr_matrix.where(~np.eye(len(corr_matrix), dtype=bool))
    max_corr = corr_matrix_masked.max().max()
    min_corr = corr_matrix_masked.min().min()
    
    max_pair = corr_matrix_masked.stack().idxmax()
    min_pair = corr_matrix_masked.stack().idxmin()
    
    print(f"\nHighest correlation: {max_corr:.3f} between {max_pair[0]} and {max_pair[1]}")
    print(f"Lowest correlation: {min_corr:.3f} between {min_pair[0]} and {min_pair[1]}")

def main():
    # Load and process data
    print("Loading and processing batch7 data...")
    df = load_and_process_data()
    
    print(f"Total batch7 direct_request records: {len(df)}")
    print(f"Unique models: {df['target_model'].nunique()}")
    print(f"Unique test cases: {df['test_case'].nunique()}")
    
    # Analyze single-turn correlations
    print("\n" + "="*50)
    print("SINGLE-TURN CORRELATION ANALYSIS")
    print("="*50)
    
    single_corr, single_pivot = create_correlation_matrix(df, 'single')
    print_summary_stats(single_corr, single_pivot, 'single')
    plot_correlation_matrix(single_corr, 'single', 
                          '/home/dcruz/multi_turn_jailbreaks/batch7_single_turn_correlations.pdf')
    
    # Analyze multi-turn correlations
    print("\n" + "="*50)
    print("MULTI-TURN CORRELATION ANALYSIS")
    print("="*50)
    
    multi_corr, multi_pivot = create_correlation_matrix(df, 'multi')
    print_summary_stats(multi_corr, multi_pivot, 'multi')
    plot_correlation_matrix(multi_corr, 'multi', 
                          '/home/dcruz/multi_turn_jailbreaks/batch7_multi_turn_correlations.pdf')
    
    # Save correlation matrices to CSV
    single_corr.to_csv('/home/dcruz/multi_turn_jailbreaks/batch7_single_turn_correlation_matrix.csv')
    multi_corr.to_csv('/home/dcruz/multi_turn_jailbreaks/batch7_multi_turn_correlation_matrix.csv')
    
    print(f"\nAnalysis complete! Correlation matrices saved as:")
    print(f"- Single-turn: batch7_single_turn_correlations.pdf")
    print(f"- Multi-turn: batch7_multi_turn_correlations.pdf")
    print(f"- CSV files: batch7_*_correlation_matrix.csv")

if __name__ == "__main__":
    main()