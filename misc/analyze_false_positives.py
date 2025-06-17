#!/usr/bin/env python3
"""
Interactive False Positive Analysis Dashboard

Creates interactive plots to analyze false positive annotations from 
clean_results/false_positive_annotations.jsonl

Plots:
1. False positive ratio by test case
2. False positive ratio by target model
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from collections import defaultdict

@st.cache_data
def load_annotations(file_path):
    """Load and parse the false positive annotations."""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return pd.DataFrame(data)

def calculate_fp_ratios_by_test_case(df):
    """Calculate false positive ratios by test case."""
    test_case_stats = df.groupby('test_case').agg({
        'decision': ['count', lambda x: (x == 'false_positive').sum()]
    }).round(3)
    
    test_case_stats.columns = ['total_annotations', 'false_positives']
    test_case_stats['false_positive_ratio'] = (
        test_case_stats['false_positives'] / test_case_stats['total_annotations']
    ).round(3)
    
    return test_case_stats.reset_index()

def calculate_fp_ratios_by_model(df):
    """Calculate false positive ratios by target model."""
    model_stats = df.groupby('target_model').agg({
        'decision': ['count', lambda x: (x == 'false_positive').sum()]
    }).round(3)
    
    model_stats.columns = ['total_annotations', 'false_positives']
    model_stats['false_positive_ratio'] = (
        model_stats['false_positives'] / model_stats['total_annotations']
    ).round(3)
    
    return model_stats.reset_index()

def create_test_case_plot(test_case_stats):
    """Create interactive bar plot for test case false positive ratios."""
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=test_case_stats['test_case'],
        y=test_case_stats['false_positive_ratio'],
        text=[f"{fp}/{total}<br>({ratio:.1%})" 
              for fp, total, ratio in zip(
                  test_case_stats['false_positives'],
                  test_case_stats['total_annotations'], 
                  test_case_stats['false_positive_ratio']
              )],
        textposition='auto',
        marker_color='lightcoral',
        hovertemplate='<b>%{x}</b><br>' +
                      'False Positive Ratio: %{y:.1%}<br>' +
                      'False Positives: %{customdata[0]}<br>' +
                      'Total Annotations: %{customdata[1]}<extra></extra>',
        customdata=test_case_stats[['false_positives', 'total_annotations']].values
    ))
    
    fig.update_layout(
        title='False Positive Ratio by Test Case',
        xaxis_title='Test Case',
        yaxis_title='False Positive Ratio',
        yaxis=dict(tickformat='.1%'),
        template='plotly_white',
        height=500
    )
    
    return fig

def create_model_plot(model_stats):
    """Create interactive bar plot for model false positive ratios."""
    # Extract just the model name (after the /)
    model_stats['model_short'] = model_stats['target_model'].str.split('/').str[-1]
    
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=model_stats['model_short'],
        y=model_stats['false_positive_ratio'],
        text=[f"{fp}/{total}<br>({ratio:.1%})" 
              for fp, total, ratio in zip(
                  model_stats['false_positives'],
                  model_stats['total_annotations'], 
                  model_stats['false_positive_ratio']
              )],
        textposition='auto',
        marker_color='lightblue',
        hovertemplate='<b>%{customdata[2]}</b><br>' +
                      'False Positive Ratio: %{y:.1%}<br>' +
                      'False Positives: %{customdata[0]}<br>' +
                      'Total Annotations: %{customdata[1]}<extra></extra>',
        customdata=model_stats[['false_positives', 'total_annotations', 'target_model']].values
    ))
    
    fig.update_layout(
        title='False Positive Ratio by Target Model',
        xaxis_title='Target Model',
        yaxis_title='False Positive Ratio',
        yaxis=dict(tickformat='.1%'),
        template='plotly_white',
        height=500,
        xaxis_tickangle=-45
    )
    
    return fig

def create_combined_breakdown(df):
    """Create a detailed breakdown table."""
    breakdown = df.groupby(['test_case', 'target_model', 'decision']).size().unstack(fill_value=0)
    if 'false_positive' not in breakdown.columns:
        breakdown['false_positive'] = 0
    if 'true_positive' not in breakdown.columns:
        breakdown['true_positive'] = 0
    
    breakdown['total'] = breakdown['false_positive'] + breakdown['true_positive']
    breakdown['fp_ratio'] = (breakdown['false_positive'] / breakdown['total']).round(3)
    
    return breakdown.reset_index()

def main():
    st.set_page_config(page_title="False Positive Analysis", layout="wide")
    
    st.title("🎯 False Positive Analysis Dashboard")
    st.markdown("Analysis of jailbreak evaluation accuracy based on human annotations")
    
    # File path
    file_path = "../clean_results/false_positive_annotations.jsonl"
    
    try:
        # Load data
        df = load_annotations(file_path)
        
        # Show basic stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Annotations", len(df))
        with col2:
            st.metric("False Positives", (df['decision'] == 'false_positive').sum())
        with col3:
            st.metric("True Positives", (df['decision'] == 'true_positive').sum())
        with col4:
            fp_rate = (df['decision'] == 'false_positive').mean()
            st.metric("Overall FP Rate", f"{fp_rate:.1%}")
        
        st.markdown("---")
        
        # Calculate ratios
        test_case_stats = calculate_fp_ratios_by_test_case(df)
        model_stats = calculate_fp_ratios_by_model(df)
        
        # Create plots
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_test_case_plot(test_case_stats), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_model_plot(model_stats), use_container_width=True)
        
        # Detailed breakdown
        st.markdown("---")
        st.subheader("📊 Detailed Breakdown")
        
        # Allow filtering
        selected_test_cases = st.multiselect(
            "Filter by test cases:",
            options=df['test_case'].unique(),
            default=df['test_case'].unique()
        )
        
        selected_models = st.multiselect(
            "Filter by models:",
            options=df['target_model'].unique(),
            default=df['target_model'].unique()
        )
        
        # Filter data
        filtered_df = df[
            (df['test_case'].isin(selected_test_cases)) &
            (df['target_model'].isin(selected_models))
        ]
        
        # Show breakdown table
        breakdown = create_combined_breakdown(filtered_df)
        st.dataframe(
            breakdown.style.format({
                'fp_ratio': '{:.1%}'
            }),
            use_container_width=True
        )
        
        # Show raw data option
        if st.checkbox("Show raw annotation data"):
            st.subheader("📋 Raw Annotations")
            display_cols = ['test_case', 'target_model', 'jailbreak_tactic', 'decision', 'note', 'evaluator']
            st.dataframe(filtered_df[display_cols], use_container_width=True)
            
    except FileNotFoundError:
        st.error(f"❌ File not found: {file_path}")
        st.info("Make sure you're running this from the repository root directory and that you have annotation data.")
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")

if __name__ == "__main__":
    main()