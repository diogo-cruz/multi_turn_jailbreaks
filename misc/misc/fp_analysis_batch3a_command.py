"""
False Positive Analysis for Batch3A Command Results

This script analyzes how false positive annotations affect Attack Success Rate (ASR)
for batch3A/command experiments, comparing ASR with and without FP consideration.

Features:
- Interactive plots using plotly
- ASR by model (with/without FP consideration)
- ASR by test case (with/without FP consideration)
- Side-by-side comparison visualizations
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path

def load_and_filter_data():
    """Load master CSV and filter for batch3A/command data."""
    csv_path = Path("../csv_results/master_results_with_fp.csv")
    df = pd.read_csv(csv_path)
    
    # Filter for batch3A and command tactic
    filtered_df = df[(df['batch'] == 'batch3A') & (df['jailbreak_tactic'] == 'command')].copy()
    
    print(f"Total batch3A/command experiments: {len(filtered_df)}")
    print(f"Experiments with FP annotations: {filtered_df['fp_decision'].notna().sum()}")
    
    return filtered_df

def calculate_asr_by_model(df):
    """Calculate ASR by model with and without FP consideration."""
    results = []
    
    for model in df['target_model'].unique():
        model_data = df[df['target_model'] == model]
        
        # Original ASR (based on goal_achieved)
        original_successes = model_data['goal_achieved'].sum()
        total_experiments = len(model_data)
        original_asr = (original_successes / total_experiments) * 100 if total_experiments > 0 else 0
        
        # Adjusted ASR (removing false positives)
        # Keep true positives and experiments without FP annotation
        fp_mask = model_data['fp_decision'] == 'false_positive'
        adjusted_successes = original_successes - fp_mask.sum()
        adjusted_asr = (adjusted_successes / total_experiments) * 100 if total_experiments > 0 else 0
        
        # Count FP annotations
        fp_count = fp_mask.sum()
        
        results.append({
            'model': model.split('/')[-1] if '/' in model else model,
            'total_experiments': total_experiments,
            'original_successes': original_successes,
            'original_asr': original_asr,
            'false_positives': fp_count,
            'adjusted_successes': adjusted_successes,
            'adjusted_asr': adjusted_asr,
            'asr_difference': original_asr - adjusted_asr
        })
    
    return pd.DataFrame(results).sort_values('original_asr', ascending=False)

def calculate_asr_by_test_case(df):
    """Calculate ASR by test case with and without FP consideration."""
    results = []
    
    for test_case in df['test_case'].unique():
        test_data = df[df['test_case'] == test_case]
        
        # Original ASR (based on goal_achieved)
        original_successes = test_data['goal_achieved'].sum()
        total_experiments = len(test_data)
        original_asr = (original_successes / total_experiments) * 100 if total_experiments > 0 else 0
        
        # Adjusted ASR (removing false positives)
        fp_mask = test_data['fp_decision'] == 'false_positive'
        adjusted_successes = original_successes - fp_mask.sum()
        adjusted_asr = (adjusted_successes / total_experiments) * 100 if total_experiments > 0 else 0
        
        # Count FP annotations
        fp_count = fp_mask.sum()
        
        results.append({
            'test_case': test_case.replace('_', ' ').title(),
            'total_experiments': total_experiments,
            'original_successes': original_successes,
            'original_asr': original_asr,
            'false_positives': fp_count,
            'adjusted_successes': adjusted_successes,
            'adjusted_asr': adjusted_asr,
            'asr_difference': original_asr - adjusted_asr
        })
    
    return pd.DataFrame(results).sort_values('original_asr', ascending=False)

def create_model_comparison_plot(model_df):
    """Create interactive plot comparing ASR by model."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('ASR by Model: Before vs After FP Removal', 'ASR Difference Due to False Positives'),
        specs=[[{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Left plot: ASR comparison
    fig.add_trace(
        go.Bar(
            name='Original ASR',
            x=model_df['model'],
            y=model_df['original_asr'],
            text=[f"{val:.1f}%" for val in model_df['original_asr']],
            textposition='auto',
            marker_color='lightcoral',
            opacity=0.8
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            name='Adjusted ASR (FP removed)',
            x=model_df['model'],
            y=model_df['adjusted_asr'],
            text=[f"{val:.1f}%" for val in model_df['adjusted_asr']],
            textposition='auto',
            marker_color='lightblue',
            opacity=0.8
        ),
        row=1, col=1
    )
    
    # Right plot: ASR difference and FP count
    fig.add_trace(
        go.Bar(
            name='ASR Difference (%)',
            x=model_df['model'],
            y=model_df['asr_difference'],
            text=[f"{val:.1f}%" for val in model_df['asr_difference']],
            textposition='auto',
            marker_color='orange',
            opacity=0.8,
            yaxis='y3'
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            name='False Positives Count',
            x=model_df['model'],
            y=model_df['false_positives'],
            mode='markers+lines+text',
            text=model_df['false_positives'],
            textposition='top center',
            marker=dict(size=10, color='red'),
            line=dict(color='red', dash='dash'),
            yaxis='y4'
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Impact of False Positive Annotations on Model ASR (Batch3A/Command)",
            x=0.5,
            font=dict(size=16)
        ),
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update x-axis
    fig.update_xaxes(title_text="Model", row=1, col=1)
    fig.update_xaxes(title_text="Model", row=1, col=2)
    
    # Update y-axes
    fig.update_yaxes(title_text="Attack Success Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="ASR Difference (%)", row=1, col=2)
    fig.update_yaxes(title_text="False Positives Count", secondary_y=True, row=1, col=2)
    
    return fig

def create_test_case_comparison_plot(test_df):
    """Create interactive plot comparing ASR by test case."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('ASR by Test Case: Before vs After FP Removal', 'ASR Difference Due to False Positives'),
        specs=[[{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Left plot: ASR comparison
    fig.add_trace(
        go.Bar(
            name='Original ASR',
            x=test_df['test_case'],
            y=test_df['original_asr'],
            text=[f"{val:.1f}%" for val in test_df['original_asr']],
            textposition='auto',
            marker_color='lightcoral',
            opacity=0.8
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            name='Adjusted ASR (FP removed)',
            x=test_df['test_case'],
            y=test_df['adjusted_asr'],
            text=[f"{val:.1f}%" for val in test_df['adjusted_asr']],
            textposition='auto',
            marker_color='lightblue',
            opacity=0.8
        ),
        row=1, col=1
    )
    
    # Right plot: ASR difference and FP count
    fig.add_trace(
        go.Bar(
            name='ASR Difference (%)',
            x=test_df['test_case'],
            y=test_df['asr_difference'],
            text=[f"{val:.1f}%" for val in test_df['asr_difference']],
            textposition='auto',
            marker_color='orange',
            opacity=0.8,
            yaxis='y3'
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            name='False Positives Count',
            x=test_df['test_case'],
            y=test_df['false_positives'],
            mode='markers+lines+text',
            text=test_df['false_positives'],
            textposition='top center',
            marker=dict(size=10, color='red'),
            line=dict(color='red', dash='dash'),
            yaxis='y4'
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Impact of False Positive Annotations on Test Case ASR (Batch3A/Command)",
            x=0.5,
            font=dict(size=16)
        ),
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update x-axis
    fig.update_xaxes(title_text="Test Case", row=1, col=1, tickangle=45)
    fig.update_xaxes(title_text="Test Case", row=1, col=2, tickangle=45)
    
    # Update y-axes
    fig.update_yaxes(title_text="Attack Success Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="ASR Difference (%)", row=1, col=2)
    fig.update_yaxes(title_text="False Positives Count", secondary_y=True, row=1, col=2)
    
    return fig

def create_summary_table(df, model_df, test_df):
    """Create summary statistics table."""
    total_experiments = len(df)
    total_successes = df['goal_achieved'].sum()
    total_fp = (df['fp_decision'] == 'false_positive').sum()
    
    print("\n" + "="*80)
    print("BATCH3A/COMMAND FALSE POSITIVE ANALYSIS SUMMARY")
    print("="*80)
    print(f"Total Experiments: {total_experiments}")
    print(f"Original Successes: {total_successes}")
    print(f"False Positives Identified: {total_fp}")
    print(f"Adjusted Successes: {total_successes - total_fp}")
    print(f"Original ASR: {(total_successes / total_experiments * 100):.1f}%")
    print(f"Adjusted ASR: {((total_successes - total_fp) / total_experiments * 100):.1f}%")
    print(f"ASR Reduction: {(total_fp / total_experiments * 100):.1f} percentage points")
    
    print(f"\nFP Annotation Coverage: {df['fp_decision'].notna().sum()}/{total_experiments} experiments ({(df['fp_decision'].notna().sum() / total_experiments * 100):.1f}%)")
    
    print("\nMODELS WITH HIGHEST FP IMPACT:")
    print("-" * 40)
    top_models = model_df.nlargest(3, 'asr_difference')[['model', 'asr_difference', 'false_positives']]
    for _, row in top_models.iterrows():
        print(f"{row['model']}: -{row['asr_difference']:.1f}% ({row['false_positives']} FPs)")
    
    print("\nTEST CASES WITH HIGHEST FP IMPACT:")
    print("-" * 40)
    top_tests = test_df.nlargest(3, 'asr_difference')[['test_case', 'asr_difference', 'false_positives']]
    for _, row in top_tests.iterrows():
        print(f"{row['test_case']}: -{row['asr_difference']:.1f}% ({row['false_positives']} FPs)")

def main():
    """Main analysis function."""
    print("Loading and analyzing batch3A/command data...")
    
    # Load data
    df = load_and_filter_data()
    
    # Calculate ASR metrics
    model_df = calculate_asr_by_model(df)
    test_df = calculate_asr_by_test_case(df)
    
    # Create visualizations
    print("\nCreating interactive plots...")
    
    model_fig = create_model_comparison_plot(model_df)
    test_fig = create_test_case_comparison_plot(test_df)
    
    # Save plots
    model_fig.write_html("misc/batch3a_command_fp_analysis_models.html")
    test_fig.write_html("misc/batch3a_command_fp_analysis_test_cases.html")
    
    # Display summary
    create_summary_table(df, model_df, test_df)
    
    print(f"\nInteractive plots saved:")
    print(f"- misc/batch3a_command_fp_analysis_models.html")
    print(f"- misc/batch3a_command_fp_analysis_test_cases.html")
    
    return model_fig, test_fig, df, model_df, test_df

if __name__ == "__main__":
    model_fig, test_fig, df, model_df, test_df = main()