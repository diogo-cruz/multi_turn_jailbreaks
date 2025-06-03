#!/usr/bin/env python3
"""
Plot ASR vs release date for multi-turn and single-turn settings.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import datetime
from dateutil import parser

# Set up matplotlib to use LaTeX
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.size': 12
})

def extract_model_family(model_name):
    """Extract model family from model name"""
    if 'deepseek' in model_name.lower():
        return 'DeepSeek'
    elif 'claude' in model_name.lower() or 'anthropic' in model_name.lower():
        return 'Anthropic'
    elif 'gemini' in model_name.lower() or 'gemma' in model_name.lower():
        return 'Google'
    elif 'llama' in model_name.lower() or 'meta' in model_name.lower():
        return 'Meta'
    elif 'mistral' in model_name.lower():
        return 'Mistral'
    elif 'qwen' in model_name.lower():
        return 'Qwen'
    elif 'gpt' in model_name.lower() or 'openai' in model_name.lower():
        return 'OpenAI'
    elif 'grok' in model_name.lower() or 'x-ai' in model_name.lower():
        return 'xAI'
    else:
        return 'Other'

def parse_release_date(date_str):
    """Parse release date string to datetime object"""
    if pd.isna(date_str) or date_str == 'Not specified':
        return None
    
    try:
        # Handle various date formats
        if 'December 2024' in date_str:
            return datetime.datetime(2024, 12, 1)
        elif 'May 2024' in date_str:
            return datetime.datetime(2024, 5, 1)
        elif 'January 2025' in date_str:
            return datetime.datetime(2025, 1, 1)
        elif 'March 2024' in date_str:
            return datetime.datetime(2024, 3, 1)
        elif 'August 2024' in date_str:
            return datetime.datetime(2024, 8, 1)
        elif 'February 2024' in date_str:
            return datetime.datetime(2024, 2, 1)
        elif 'October 2024' in date_str:
            return datetime.datetime(2024, 10, 1)
        elif 'November 2024' in date_str:
            return datetime.datetime(2024, 11, 1)
        elif 'September 2024' in date_str:
            return datetime.datetime(2024, 9, 1)
        elif 'June 2024' in date_str:
            return datetime.datetime(2024, 6, 1)
        elif 'July 2024' in date_str:
            return datetime.datetime(2024, 7, 1)
        elif 'December 2023' in date_str:
            return datetime.datetime(2023, 12, 1)
        else:
            # Try to parse with dateutil
            return parser.parse(date_str)
    except:
        return None

def calculate_asr(df, temp=0.0):
    """
    Calculate Attack Success Rate (maximum over tactics, average over test cases, temp 0)
    """
    # Filter for temperature 0
    df_temp = df[df['target_temp'] == temp].copy()
    
    # Group by model, turn_type, and tactic, then calculate ASR per tactic
    asr_by_tactic = (df_temp.groupby(['target_model', 'turn_type', 'jailbreak_tactic'])['goal_achieved']
                     .mean().reset_index())
    
    # Take maximum ASR over tactics for each model and turn type
    max_asr = (asr_by_tactic.groupby(['target_model', 'turn_type'])['goal_achieved']
               .max().reset_index())
    
    return max_asr

def main():
    # Import utilities
    from model_utils import get_model_data_with_info
    
    # Load data
    df = pd.read_csv('../../csv_results/master_results.csv')
    model_info = pd.read_csv('../../model_comparison.csv')
    
    # Calculate ASR
    asr_data = calculate_asr(df)
    
    # Merge with model information
    asr_with_info_raw = get_model_data_with_info(asr_data, model_info, ['Release Date'])
    
    # Parse release dates and filter valid ones
    asr_with_info = []
    for row in asr_with_info_raw:
        release_date = parse_release_date(row['release_date'])
        if release_date is not None:
            row_with_date = row.copy()
            row_with_date['release_date'] = release_date
            asr_with_info.append(row_with_date)
    
    asr_df = pd.DataFrame(asr_with_info)
    
    # Check if we have data
    if asr_df.empty:
        print("Warning: No data available for release date plot")
        print("Check human_TODO.md for missing model information")
        return
    
    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    # Get unique families and assign colors
    families = sorted(asr_df['family'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(families)))
    family_colors = dict(zip(families, colors))
    
    # Plot for each family and turn type
    for family in families:
        family_data = asr_df[asr_df['family'] == family]
        
        # Multi-turn (solid line)
        multi_data = family_data[family_data['turn_type'] == 'multi']
        if not multi_data.empty:
            multi_sorted = multi_data.sort_values('release_date')
            ax.plot(multi_sorted['release_date'], multi_sorted['asr'], 
                   color=family_colors[family], linestyle='-', marker='o',
                   label=f'{family} (Multi-turn)', linewidth=2, markersize=6)
        
        # Single-turn (dashed line)
        single_data = family_data[family_data['turn_type'] == 'single']
        if not single_data.empty:
            single_sorted = single_data.sort_values('release_date')
            ax.plot(single_sorted['release_date'], single_sorted['asr'], 
                   color=family_colors[family], linestyle='--', marker='s',
                   label=f'{family} (Single-turn)', linewidth=2, markersize=6)
    
    # Customize plot
    ax.set_xlabel('Release Date')
    ax.set_ylabel('Attack Success Rate (ASR)')
    ax.set_title('Attack Success Rate vs Model Release Date')
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_ylim(0, 1)
    
    # Format x-axis dates
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'asr_vs_release_date.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'asr_vs_release_date.png', dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_dir / 'asr_vs_release_date.pdf'}")
    
    plt.show()

if __name__ == '__main__':
    main() 