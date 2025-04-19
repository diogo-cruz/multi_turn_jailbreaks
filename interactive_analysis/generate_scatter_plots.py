import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import re
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.dates as mdates
from datetime import datetime

# Define output directory for figures
FIGURES_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

# Define color mapping for companies
COMPANY_COLORS = {
    'Google': '#4285F4',  # Google Blue
    'Meta': '#1877F2',    # Facebook Blue
    'Anthropic': '#EE524F', # Red-ish
    'Mistral AI': '#673AB7', # Purple
    'DeepSeek': '#FF9800', # Orange
    'Alibaba': '#FF4E00',  # Alibaba Orange
    'xAI': '#000000',      # Black
    'OpenAI': '#00A67E',   # OpenAI Teal
    'Default': '#888888'   # Gray for unknown
}

# Helper function to save figures
def save_figure(fig, filename):
    """Save figure as PNG and PDF"""
    png_path = os.path.join(FIGURES_DIR, f"{filename}.png")
    pdf_path = os.path.join(FIGURES_DIR, f"{filename}.pdf")
    
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    
    print(f"Saved figure to {png_path} and {pdf_path}")

def parse_release_date(date_str):
    """Parse various date formats into datetime objects"""
    if not date_str or pd.isna(date_str):
        return None
    
    # Format 1: "Month Year" (e.g., "May 2023")
    month_year_pattern = r'^(\w+)\s+(\d{4})$'
    match = re.match(month_year_pattern, date_str)
    if match:
        month_names = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = month_names.get(match.group(1), 1)  # Default to January if not found
        year = int(match.group(2))
        return datetime(year, month, 1)
    
    # Format 2: "YYYY-MM-DD" or "YYYY/MM/DD"
    iso_date_pattern = r'^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})$'
    match = re.match(iso_date_pattern, date_str)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return datetime(year, month, day)
    
    # If all else fails, return None
    print(f"Could not parse date: {date_str}")
    return None

def get_company_from_model(model_name):
    """Extract company name from model name"""
    if pd.isna(model_name):
        return "Unknown"
    
    model_lower = model_name.lower()
    
    if 'google' in model_lower or 'gemini' in model_lower or 'gemma' in model_lower:
        return 'Google'
    elif 'meta' in model_lower or 'llama' in model_lower:
        return 'Meta'
    elif 'anthropic' in model_lower or 'claude' in model_lower:
        return 'Anthropic'
    elif 'mistral' in model_lower:
        return 'Mistral AI'
    elif 'deepseek' in model_lower:
        return 'DeepSeek'
    elif 'qwen' in model_lower:
        return 'Alibaba'
    elif 'x-ai' in model_lower or 'grok' in model_lower:
        return 'xAI'
    elif 'openai' in model_lower or 'gpt' in model_lower:
        return 'OpenAI'
    else:
        return 'Unknown'

def plot_asr_vs_size(enhanced_data_df, model_comparison_df, filename_prefix='asr_vs_size'):
    """Generate scatter plot of ASR vs model size"""
    # Merge the datasets
    model_data = {}
    
    # Process model comparison data
    for _, row in model_comparison_df.iterrows():
        model_name = row['Model']
        model_data[model_name] = {
            'size': row['Parameters'],
            'company': row['Company'],
            'release_date': parse_release_date(row['Release Date']),
            'models': []  # Will hold full model names from enhanced data
        }
    
    # Extract unique models and success rates from enhanced data
    models = enhanced_data_df['target_model'].unique()
    model_success = {}
    
    for model in models:
        success_rate = enhanced_data_df[enhanced_data_df['target_model'] == model]['goal_achieved'].mean() * 100
        model_success[model] = success_rate
        
        # Find matching model in model_data
        model_match = None
        model_short = model.split('/')[-1] if '/' in model else model
        
        for comp_model in model_data:
            comp_short = comp_model.split('/')[-1] if '/' in comp_model else comp_model
            if model_short.lower() == comp_short.lower():
                model_match = comp_model
                break
        
        if model_match:
            model_data[model_match]['models'].append(model)
        else:
            # If no match found, try to extract company and create a new entry
            company = get_company_from_model(model)
            # Try to extract size from model name if available
            size_match = re.search(r'(\d+)[bB]', model_short)
            size = float(size_match.group(1)) if size_match else None
            
            if size:
                model_data[model] = {
                    'size': size,
                    'company': company,
                    'release_date': None,
                    'models': [model]
                }
    
    # Prepare plot data
    plot_data = []
    
    for base_model, data in model_data.items():
        if not data['models']:  # Skip if no actual models mapped to this base model
            continue
        
        # Calculate average success rate for all mapped models
        avg_success = np.mean([model_success.get(model, 0) for model in data['models']])
        
        plot_data.append({
            'name': base_model.split('/')[-1] if '/' in base_model else base_model,
            'size': data['size'],
            'company': data['company'],
            'success_rate': avg_success,
            'full_name': base_model
        })
    
    # Filter out entries without size data
    plot_data = [d for d in plot_data if d['size'] is not None]
    
    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    
    # Plot points by company with different colors
    for company in set(d['company'] for d in plot_data):
        company_data = [d for d in plot_data if d['company'] == company]
        
        # Get color for company
        color = COMPANY_COLORS.get(company, COMPANY_COLORS['Default'])
        
        x = [d['size'] for d in company_data]
        y = [d['success_rate'] for d in company_data]
        labels = [d['name'] for d in company_data]
        
        plt.scatter(x, y, c=color, label=company, s=100, alpha=0.7)
        
        # Add model names as annotations
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (x[i], y[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center'
            )
    
    # Add trend line
    sizes = [d['size'] for d in plot_data]
    success_rates = [d['success_rate'] for d in plot_data]
    
    if len(sizes) > 1:
        z = np.polyfit(np.log10(sizes), success_rates, 1)
        p = np.poly1d(z)
        x_trend = np.logspace(np.log10(min(sizes)), np.log10(max(sizes)), 100)
        plt.plot(x_trend, p(np.log10(x_trend)), 'k--', alpha=0.5)
    
    # Set up log scale x-axis
    plt.xscale('log')
    plt.grid(True, which="both", ls="-", alpha=0.2)
    
    # Customize the plot
    plt.xlabel('Model Size (Billion Parameters)', fontsize=12)
    plt.ylabel('Attack Success Rate (%)', fontsize=12)
    plt.title('Attack Success Rate vs. Model Size', fontsize=14)
    plt.legend(title='Company')
    
    # Add horizontal line at 50%
    plt.axhline(y=50, color='r', linestyle=':', alpha=0.5)
    
    # Set axis limits
    plt.ylim(0, 100)
    plt.xlim(min(sizes) * 0.5, max(sizes) * 2)
    
    plt.tight_layout()
    fig = plt.gcf()
    save_figure(fig, filename_prefix)

def plot_asr_vs_date(enhanced_data_df, model_comparison_df, filename_prefix='asr_vs_date'):
    """Generate scatter plot of ASR vs release date"""
    # Merge the datasets
    model_data = {}
    
    # Process model comparison data
    for _, row in model_comparison_df.iterrows():
        model_name = row['Model']
        release_date = parse_release_date(row['Release Date'])
        
        if release_date:  # Only include models with valid dates
            model_data[model_name] = {
                'size': row['Parameters'],
                'company': row['Company'],
                'release_date': release_date,
                'models': []  # Will hold full model names from enhanced data
            }
    
    # Extract unique models and success rates from enhanced data
    models = enhanced_data_df['target_model'].unique()
    model_success = {}
    
    for model in models:
        success_rate = enhanced_data_df[enhanced_data_df['target_model'] == model]['goal_achieved'].mean() * 100
        model_success[model] = success_rate
        
        # Find matching model in model_data
        model_match = None
        model_short = model.split('/')[-1] if '/' in model else model
        
        for comp_model in model_data:
            comp_short = comp_model.split('/')[-1] if '/' in comp_model else comp_model
            if model_short.lower() == comp_short.lower():
                model_match = comp_model
                break
        
        if model_match:
            model_data[model_match]['models'].append(model)
    
    # Prepare plot data
    plot_data = []
    
    for base_model, data in model_data.items():
        if not data['models'] or not data['release_date']:
            continue
        
        # Calculate average success rate for all mapped models
        avg_success = np.mean([model_success.get(model, 0) for model in data['models']])
        
        plot_data.append({
            'name': base_model.split('/')[-1] if '/' in base_model else base_model,
            'release_date': data['release_date'],
            'company': data['company'],
            'success_rate': avg_success,
            'full_name': base_model,
            'size': data['size']
        })
    
    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    
    # Plot points by company with different colors
    for company in set(d['company'] for d in plot_data):
        company_data = [d for d in plot_data if d['company'] == company]
        
        # Get color for company
        color = COMPANY_COLORS.get(company, COMPANY_COLORS['Default'])
        
        x = [d['release_date'] for d in company_data]
        y = [d['success_rate'] for d in company_data]
        labels = [d['name'] for d in company_data]
        sizes = [d['size'] * 2 for d in company_data]  # Scale marker size by model size
        
        plt.scatter(x, y, c=color, label=company, s=sizes, alpha=0.7)
        
        # Add model names as annotations
        for i, label in enumerate(labels):
            plt.annotate(
                label,
                (x[i], y[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center'
            )
    
    # Format the x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.gcf().autofmt_xdate()
    
    # Customize the plot
    plt.grid(True, alpha=0.2)
    plt.xlabel('Release Date', fontsize=12)
    plt.ylabel('Attack Success Rate (%)', fontsize=12)
    plt.title('Attack Success Rate vs. Release Date', fontsize=14)
    plt.legend(title='Company')
    
    # Add horizontal line at 50%
    plt.axhline(y=50, color='r', linestyle=':', alpha=0.5)
    
    # Set y-axis limits
    plt.ylim(0, 100)
    
    plt.tight_layout()
    fig = plt.gcf()
    save_figure(fig, filename_prefix)

def main():
    """Main function to generate scatter plots"""
    print("Starting scatter plot generation...")
    
    try:
        # Load enhanced master data
        enhanced_data_df = pd.read_csv('enhanced_master_data.csv')
        
        # Load model comparison data
        model_comparison_df = pd.read_csv('model_comparison.csv')
        
        # Generate ASR vs Size plot
        plot_asr_vs_size(enhanced_data_df, model_comparison_df, 'enhanced_master_data_asr_vs_size')
        
        # Generate ASR vs Date plot
        plot_asr_vs_date(enhanced_data_df, model_comparison_df, 'enhanced_master_data_asr_vs_date')
        
        print("Scatter plot generation complete!")
    except Exception as e:
        print(f"Error generating scatter plots: {e}")

if __name__ == "__main__":
    main() 