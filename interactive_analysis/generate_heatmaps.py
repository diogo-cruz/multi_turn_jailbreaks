import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import re
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

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

def generate_asr_heatmap(df, turn_type=None, filename_prefix='asr_heatmap'):
    """Generate ASR heatmap of test cases vs tactics"""
    # Filter by turn type if specified
    if turn_type:
        df = df[df['turn_type'] == turn_type]
        filename_prefix += f"_{turn_type}"
    
    # Create pivot table of ASR values
    pivot = pd.pivot_table(
        df, 
        values='goal_achieved',
        index='test_case', 
        columns='jailbreak_tactic',
        aggfunc=lambda x: np.mean(x) * 100  # Convert to percentage
    )
    
    # Set up plot
    plt.figure(figsize=(16, 12))
    
    # Create a custom colormap from white to red
    colormap = LinearSegmentedColormap.from_list(
        "white_yellow_red", [(0, "#FFFFFF"), (0.5, "#FFFF00"), (1, "#FF0000")]
    )
    
    # Plot heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=colormap,
        linewidths=0.5,
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Attack Success Rate (%)'}
    )
    
    title = 'Attack Success Rate (%) by Test Case and Tactic'
    if turn_type:
        title += f" - {turn_type.capitalize()} Turn"
    
    plt.title(title, fontsize=14)
    plt.tight_layout()
    
    fig = plt.gcf()
    save_figure(fig, f"{filename_prefix}")

def generate_refused_heatmap(df, turn_type=None, filename_prefix='refused_heatmap'):
    """Generate refusal count heatmap of test cases vs tactics"""
    # Filter by turn type if specified
    if turn_type:
        df = df[df['turn_type'] == turn_type]
        filename_prefix += f"_{turn_type}"
    
    # Create pivot table of refused counts
    pivot = pd.pivot_table(
        df, 
        values='refused',
        index='test_case', 
        columns='jailbreak_tactic',
        aggfunc=np.mean  # Average refusal count
    )
    
    # Set up plot
    plt.figure(figsize=(16, 12))
    
    # Create a custom colormap from white to blue
    colormap = LinearSegmentedColormap.from_list(
        "white_blue", [(0, "#FFFFFF"), (1, "#0000FF")]
    )
    
    # Plot heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=colormap,
        linewidths=0.5,
        cbar_kws={'label': 'Average Refusal Count'}
    )
    
    title = 'Average Refusal Count by Test Case and Tactic'
    if turn_type:
        title += f" - {turn_type.capitalize()} Turn"
    
    plt.title(title, fontsize=14)
    plt.tight_layout()
    
    fig = plt.gcf()
    save_figure(fig, f"{filename_prefix}")

def generate_round_heatmap(df, turn_type=None, filename_prefix='round_heatmap'):
    """Generate max round count heatmap of test cases vs tactics"""
    # Filter by turn type if specified
    if turn_type:
        df = df[df['turn_type'] == turn_type]
        filename_prefix += f"_{turn_type}"
    
    # Create pivot table of max round counts
    pivot = pd.pivot_table(
        df, 
        values='max_round',
        index='test_case', 
        columns='jailbreak_tactic',
        aggfunc=np.mean  # Average max round
    )
    
    # Set up plot
    plt.figure(figsize=(16, 12))
    
    # Create a custom colormap from white to green
    colormap = LinearSegmentedColormap.from_list(
        "white_green", [(0, "#FFFFFF"), (1, "#00AA00")]
    )
    
    # Plot heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=colormap,
        linewidths=0.5,
        cbar_kws={'label': 'Average Conversation Rounds'}
    )
    
    title = 'Average Conversation Rounds by Test Case and Tactic'
    if turn_type:
        title += f" - {turn_type.capitalize()} Turn"
    
    plt.title(title, fontsize=14)
    plt.tight_layout()
    
    fig = plt.gcf()
    save_figure(fig, f"{filename_prefix}")

def generate_model_comparison_heatmap(df, value_col, title, filename_prefix):
    """Generate model comparison heatmap"""
    # Get unique models and test cases
    models = df['target_model'].unique()
    test_cases = df['test_case'].unique()
    
    # Create shorter model names for display
    model_display = {model: model.split('/')[-1] if '/' in model else model for model in models}
    
    # Create a new dataframe for the heatmap
    heatmap_data = []
    
    for model in models:
        for test_case in test_cases:
            subset = df[(df['target_model'] == model) & (df['test_case'] == test_case)]
            if not subset.empty:
                value = subset[value_col].mean()
                heatmap_data.append({
                    'model': model_display[model],
                    'test_case': test_case,
                    'value': value
                })
    
    if not heatmap_data:
        print(f"No data for heatmap {filename_prefix}")
        return
    
    # Convert to dataframe and pivot
    heatmap_df = pd.DataFrame(heatmap_data)
    pivot = heatmap_df.pivot(index='model', columns='test_case', values='value')
    
    # Set up plot
    plt.figure(figsize=(18, 12))
    
    # Determine colormap based on value type
    if value_col == 'goal_achieved':
        # For ASR, use white to red and multiply by 100 for percentage
        colormap = LinearSegmentedColormap.from_list(
            "white_yellow_red", [(0, "#FFFFFF"), (0.5, "#FFFF00"), (1, "#FF0000")]
        )
        pivot = pivot * 100
        fmt = ".1f"
        vmin = 0
        vmax = 100
        cbar_label = 'Success Rate (%)'
    elif value_col == 'refused':
        # For refusal, use white to blue
        colormap = LinearSegmentedColormap.from_list(
            "white_blue", [(0, "#FFFFFF"), (1, "#0000FF")]
        )
        fmt = ".1f"
        vmin = None
        vmax = None
        cbar_label = 'Average Refusal Count'
    else:  # max_round
        # For rounds, use white to green
        colormap = LinearSegmentedColormap.from_list(
            "white_green", [(0, "#FFFFFF"), (1, "#00AA00")]
        )
        fmt = ".1f"
        vmin = None
        vmax = None
        cbar_label = 'Average Conversation Rounds'
    
    # Plot heatmap
    sns.heatmap(
        pivot,
        annot=True,
        fmt=fmt,
        cmap=colormap,
        linewidths=0.5,
        vmin=vmin,
        vmax=vmax,
        cbar_kws={'label': cbar_label}
    )
    
    plt.title(title, fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    fig = plt.gcf()
    save_figure(fig, filename_prefix)

def main():
    """Main function to generate all heatmaps"""
    print("Starting heatmap generation...")
    
    # Define CSV files to process
    data_files = [
        'results_test_runs.csv', 
        'results_2D.csv', 
        'results_2D_2.csv', 
        'results_2B.csv',
        'results_final_3samples.csv',
        'enhanced_master_data.csv'
    ]
    
    # Process each file
    for file_name in data_files:
        print(f"Processing {file_name}...")
        file_prefix = file_name.replace('.csv', '')
        
        try:
            df = load_data(file_name)
            
            # Generate heatmaps for all data
            generate_asr_heatmap(df, None, f"{file_prefix}_asr")
            generate_refused_heatmap(df, None, f"{file_prefix}_refused")
            generate_round_heatmap(df, None, f"{file_prefix}_round")
            
            # Generate heatmaps for single-turn data
            generate_asr_heatmap(df, 'single', f"{file_prefix}_asr")
            generate_refused_heatmap(df, 'single', f"{file_prefix}_refused")
            generate_round_heatmap(df, 'single', f"{file_prefix}_round")
            
            # Generate heatmaps for multi-turn data
            generate_asr_heatmap(df, 'multi', f"{file_prefix}_asr")
            generate_refused_heatmap(df, 'multi', f"{file_prefix}_refused")
            generate_round_heatmap(df, 'multi', f"{file_prefix}_round")
            
            # Generate model comparison heatmaps
            generate_model_comparison_heatmap(
                df, 
                'goal_achieved', 
                'Attack Success Rate (%) by Model and Test Case', 
                f"{file_prefix}_model_test_case_asr"
            )
            
            generate_model_comparison_heatmap(
                df, 
                'refused', 
                'Average Refusal Count by Model and Test Case', 
                f"{file_prefix}_model_test_case_refused"
            )
            
            generate_model_comparison_heatmap(
                df, 
                'max_round', 
                'Average Conversation Rounds by Model and Test Case', 
                f"{file_prefix}_model_test_case_round"
            )
            
            print(f"Completed processing {file_name}")
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    print("Heatmap generation complete!")

if __name__ == "__main__":
    main() 