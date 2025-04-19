import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import re
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

# Define output directory for figures
FIGURES_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# Function to parse score list strings into actual python lists
def parse_scores(scores_str):
    if not scores_str or pd.isna(scores_str) or scores_str == '[]':
        return []
    
    # Handle different string formats
    if isinstance(scores_str, str):
        # Replace single quotes with double quotes for valid JSON
        scores_str = scores_str.replace("'", '"')
        try:
            # Try parsing as JSON
            return json.loads(scores_str)
        except json.JSONDecodeError:
            # If that fails, try a regex approach
            pattern = r'\[(.*)\]'
            match = re.search(pattern, scores_str)
            if match:
                values = match.group(1).split(',')
                return [float(val.strip()) for val in values if val.strip()]
            return []
    return scores_str  # Already a list or other object

# Calculate Attack Success Rate (ASR)
def calculate_asr(subset):
    """Calculate the Attack Success Rate for a subset of data"""
    if subset.empty:
        return 0.0
    
    success_count = subset['goal_achieved'].apply(
        lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x)
    ).sum()
    
    return (success_count / len(subset)) * 100

# Helper function to save figures
def save_figure(fig, filename):
    """Save figure as PNG and PDF"""
    png_path = os.path.join(FIGURES_DIR, f"{filename}.png")
    pdf_path = os.path.join(FIGURES_DIR, f"{filename}.pdf")
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    
    print(f"Saved figure to {png_path} and {pdf_path}")

def load_data(file_path):
    """Load and preprocess CSV data"""
    df = pd.read_csv(file_path)
    
    # Convert goal_achieved to boolean
    if 'goal_achieved' in df.columns:
        df['goal_achieved'] = df['goal_achieved'].apply(
            lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x)
        )
    
    # Parse scores
    if 'scores' in df.columns:
        df['scores'] = df['scores'].apply(parse_scores)
        df['avg_score'] = df['scores'].apply(lambda x: sum(x) / len(x) if len(x) > 0 else 0)
    
    return df

def plot_model_success_rates(df, filename_prefix='model_success_rates'):
    """Plot success rates per model"""
    # Group by model and calculate success rate
    model_success = df.groupby('target_model')['goal_achieved'].mean() * 100
    model_success = model_success.reset_index().sort_values('goal_achieved', ascending=False)
    
    # Get shorter model names for cleaner plots
    model_success['short_name'] = model_success['target_model'].apply(
        lambda x: x.split('/')[-1] if '/' in x else x
    )
    
    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(model_success['short_name'], model_success['goal_achieved'], color='#4285F4')
    
    # Add value labels
    for i, v in enumerate(model_success['goal_achieved']):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    ax.set_xlabel('Success Rate (%)')
    ax.set_title('Attack Success Rate by Model')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_test_case_success_rates(df, filename_prefix='test_case_success_rates'):
    """Plot success rates per test case"""
    # Group by test case and calculate success rate
    test_case_success = df.groupby('test_case')['goal_achieved'].mean() * 100
    test_case_success = test_case_success.reset_index().sort_values('goal_achieved', ascending=False)
    
    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(test_case_success['test_case'], test_case_success['goal_achieved'], color='#EA4335')
    
    # Add value labels
    for i, v in enumerate(test_case_success['goal_achieved']):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    ax.set_xlabel('Success Rate (%)')
    ax.set_title('Attack Success Rate by Test Case')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_tactic_success_rates(df, filename_prefix='tactic_success_rates'):
    """Plot success rates per jailbreak tactic"""
    # Group by tactic and calculate success rate
    tactic_success = df.groupby('jailbreak_tactic')['goal_achieved'].mean() * 100
    tactic_success = tactic_success.reset_index().sort_values('goal_achieved', ascending=False)
    
    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(tactic_success['jailbreak_tactic'], tactic_success['goal_achieved'], color='#FBBC05')
    
    # Add value labels
    for i, v in enumerate(tactic_success['goal_achieved']):
        ax.text(v + 1, i, f"{v:.1f}%", va='center')
    
    ax.set_xlabel('Success Rate (%)')
    ax.set_title('Attack Success Rate by Jailbreak Tactic')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_turn_type_success_rates(df, filename_prefix='turn_type_success_rates'):
    """Plot success rates per turn type (single vs multi)"""
    # Group by turn type and calculate success rate
    turn_success = df.groupby('turn_type')['goal_achieved'].mean() * 100
    turn_success = turn_success.reset_index().sort_values('goal_achieved', ascending=False)
    
    # Plot bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(turn_success['turn_type'], turn_success['goal_achieved'], color=['#34A853', '#4285F4'])
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f"{height:.1f}%", ha='center', va='bottom')
    
    ax.set_ylabel('Success Rate (%)')
    ax.set_title('Attack Success Rate by Turn Type')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_heatmap(df, filename_prefix='heatmap'):
    """Plot heatmap of test cases vs tactics"""
    # Create pivot table
    pivot = pd.pivot_table(
        df, 
        values='goal_achieved',
        index='test_case', 
        columns='jailbreak_tactic',
        aggfunc=lambda x: np.mean(x) * 100  # Convert to percentage
    )
    
    # Set up plot
    plt.figure(figsize=(14, 10))
    
    # Create a custom colormap from blue to red
    colormap = LinearSegmentedColormap.from_list(
        "blue_white_red", [(0, "#FFFFFF"), (0.5, "#FFFF00"), (1, "#FF0000")]
    )
    
    # Plot heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=colormap,
        linewidths=0.5,
        vmin=0,
        vmax=100
    )
    
    plt.title('Attack Success Rate (%) by Test Case and Tactic')
    plt.tight_layout()
    
    fig = plt.gcf()
    save_figure(fig, f"{filename_prefix}")

def plot_test_case_size_chart(df, model_comparison_df, filename_prefix='test_case_size'):
    """Plot test case success rate vs model size"""
    # Create model size mapping
    model_sizes = {}
    for _, row in model_comparison_df.iterrows():
        model_name = row['Model']
        # Extract model name from full path if necessary
        short_name = model_name.split('/')[-1] if '/' in model_name else model_name
        model_sizes[short_name] = row['Parameters']
    
    # Add size to main dataframe
    df['model_short_name'] = df['target_model'].apply(lambda x: x.split('/')[-1] if '/' in x else x)
    df['model_size'] = df['model_short_name'].map(model_sizes)
    
    # For each test case, plot success rate vs model size
    test_cases = df['test_case'].unique()
    
    # Create subplots grid based on number of test cases
    n_cols = 3
    n_rows = (len(test_cases) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows))
    axes = axes.flatten()
    
    for i, test_case in enumerate(test_cases):
        if i < len(axes):
            ax = axes[i]
            test_data = df[df['test_case'] == test_case]
            
            # Group by model size and calculate mean success rate
            size_group = test_data.groupby('model_size')['goal_achieved'].mean() * 100
            size_group = size_group.reset_index()
            
            # Sort by size for line plot
            size_group = size_group.sort_values('model_size')
            
            # Plot
            ax.plot(size_group['model_size'], size_group['goal_achieved'], 'o-', linewidth=2)
            ax.set_title(test_case)
            ax.set_xlabel('Model Size (B parameters)')
            ax.set_ylabel('Success Rate (%)')
            ax.grid(linestyle='--', alpha=0.7)
            
            # Use log scale for x-axis
            ax.set_xscale('log')
            ax.set_ylim(0, 100)
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_tactic_size_chart(df, model_comparison_df, filename_prefix='tactic_size'):
    """Plot jailbreak tactic success rate vs model size"""
    # Create model size mapping
    model_sizes = {}
    for _, row in model_comparison_df.iterrows():
        model_name = row['Model']
        # Extract model name from full path if necessary
        short_name = model_name.split('/')[-1] if '/' in model_name else model_name
        model_sizes[short_name] = row['Parameters']
    
    # Add size to main dataframe
    df['model_short_name'] = df['target_model'].apply(lambda x: x.split('/')[-1] if '/' in x else x)
    df['model_size'] = df['model_short_name'].map(model_sizes)
    
    # For each tactic, plot success rate vs model size
    tactics = df['jailbreak_tactic'].unique()
    
    # Create subplots grid based on number of tactics
    n_cols = 3
    n_rows = (len(tactics) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows))
    axes = axes.flatten()
    
    for i, tactic in enumerate(tactics):
        if i < len(axes):
            ax = axes[i]
            tactic_data = df[df['jailbreak_tactic'] == tactic]
            
            # Group by model size and calculate mean success rate
            size_group = tactic_data.groupby('model_size')['goal_achieved'].mean() * 100
            size_group = size_group.reset_index()
            
            # Sort by size for line plot
            size_group = size_group.sort_values('model_size')
            
            # Plot
            ax.plot(size_group['model_size'], size_group['goal_achieved'], 'o-', linewidth=2)
            ax.set_title(tactic)
            ax.set_xlabel('Model Size (B parameters)')
            ax.set_ylabel('Success Rate (%)')
            ax.grid(linestyle='--', alpha=0.7)
            
            # Use log scale for x-axis
            ax.set_xscale('log')
            ax.set_ylim(0, 100)
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_refused_counts(df, filename_prefix='refused_counts'):
    """Plot average refusal counts by model"""
    # Group by model and calculate mean refusal
    model_refusal = df.groupby('target_model')['refused'].mean()
    model_refusal = model_refusal.reset_index().sort_values('refused', ascending=False)
    
    # Get shorter model names for cleaner plots
    model_refusal['short_name'] = model_refusal['target_model'].apply(
        lambda x: x.split('/')[-1] if '/' in x else x
    )
    
    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(model_refusal['short_name'], model_refusal['refused'], color='#EA4335')
    
    # Add value labels
    for i, v in enumerate(model_refusal['refused']):
        ax.text(v + 0.1, i, f"{v:.1f}", va='center')
    
    ax.set_xlabel('Average Refusal Count')
    ax.set_title('Average Refusal Count by Model')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def plot_max_round_counts(df, filename_prefix='max_round_counts'):
    """Plot average max round counts by model"""
    # Group by model and calculate mean max_round
    model_rounds = df.groupby('target_model')['max_round'].mean()
    model_rounds = model_rounds.reset_index().sort_values('max_round', ascending=False)
    
    # Get shorter model names for cleaner plots
    model_rounds['short_name'] = model_rounds['target_model'].apply(
        lambda x: x.split('/')[-1] if '/' in x else x
    )
    
    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(model_rounds['short_name'], model_rounds['max_round'], color='#34A853')
    
    # Add value labels
    for i, v in enumerate(model_rounds['max_round']):
        ax.text(v + 0.1, i, f"{v:.1f}", va='center')
    
    ax.set_xlabel('Average Max Round Count')
    ax.set_title('Average Conversation Rounds by Model')
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    save_figure(fig, f"{filename_prefix}")

def main():
    """Main function to generate all plots"""
    print("Starting plot generation...")
    
    # Define CSV files to process
    data_files = [
        'results_test_runs.csv', 
        'results_2D.csv', 
        'results_2D_2.csv', 
        'results_2B.csv',
        'results_final_3samples.csv',
        'enhanced_master_data.csv'
    ]
    
    # Load model comparison data for size charts
    model_comparison_df = pd.read_csv('model_comparison.csv')
    
    # Process each file
    for file_name in data_files:
        print(f"Processing {file_name}...")
        file_prefix = file_name.replace('.csv', '')
        
        try:
            df = load_data(file_name)
            
            # Generate all plot types for this dataset
            plot_model_success_rates(df, f"{file_prefix}_model_success")
            plot_test_case_success_rates(df, f"{file_prefix}_test_case_success")
            plot_tactic_success_rates(df, f"{file_prefix}_tactic_success")
            plot_turn_type_success_rates(df, f"{file_prefix}_turn_type_success")
            plot_heatmap(df, f"{file_prefix}_heatmap")
            plot_refused_counts(df, f"{file_prefix}_refused_counts")
            plot_max_round_counts(df, f"{file_prefix}_max_round_counts")
            
            # Size charts require the model comparison data
            plot_test_case_size_chart(df, model_comparison_df, f"{file_prefix}_test_case_size")
            plot_tactic_size_chart(df, model_comparison_df, f"{file_prefix}_tactic_size")
            
            print(f"Completed processing {file_name}")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    print("Plot generation complete!")

if __name__ == "__main__":
    main() 