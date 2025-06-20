#!/usr/bin/env python3
"""
Batch3A Interactive Dashboard

Creates comprehensive interactive plots for batch3A analysis showing:
1. ASR by Model (with/without FP consideration)
2. ASR by Test Case (with/without FP consideration)  
3. ASR by Tactic (with/without FP consideration)
4. ASR by Test Case + Tactic combination (with/without FP consideration)

All plots show the impact of false positive evaluation on attack success rates.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path
import numpy as np

@st.cache_data
def load_batch3a_data():
    """Load batch3A CSV data with complete FP annotations."""
    csv_path = "../csv_results/batch3A_complete_fp.csv"
    df = pd.read_csv(csv_path)
    # Drop the unnamed index column if it exists
    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)
    return df

def calculate_asr_by_dimension(df, dimension_col):
    """Calculate ASR by any dimension with and without FP consideration, split by turn type."""
    results = []
    
    for dimension in df[dimension_col].unique():
        if pd.isna(dimension):
            continue
        
        for turn_type in ['single', 'multi']:
            dim_data = df[(df[dimension_col] == dimension) & (df['turn_type'] == turn_type)]
            
            if len(dim_data) == 0:
                continue
            
            # Original ASR (based on goal_achieved)
            original_successes = dim_data['goal_achieved'].sum()
            total_experiments = len(dim_data)
            original_asr = (original_successes / total_experiments) * 100 if total_experiments > 0 else 0
            
            # Adjusted ASR (removing false positives)
            # Only count FP among successful attacks
            successful_data = dim_data[dim_data['goal_achieved'] == True]
            fp_mask = successful_data['fp_decision'] == 'false_positive'
            fp_count = fp_mask.sum()
            adjusted_successes = original_successes - fp_count
            adjusted_asr = (adjusted_successes / total_experiments) * 100 if total_experiments > 0 else 0
            
            results.append({
                dimension_col: dimension,
                'turn_type': turn_type,
                'total_experiments': total_experiments,
                'original_successes': original_successes,
                'original_asr': original_asr,
                'false_positives': fp_count,
                'adjusted_successes': adjusted_successes,
                'adjusted_asr': adjusted_asr,
                'asr_difference': original_asr - adjusted_asr
            })
    
    return pd.DataFrame(results).sort_values(['original_asr', 'turn_type'], ascending=[False, True])

def calculate_asr_by_combination(df):
    """Calculate ASR by test case + tactic combination, split by turn type."""
    results = []
    
    for test_case in df['test_case'].unique():
        for tactic in df['jailbreak_tactic'].unique():
            for turn_type in ['single', 'multi']:
                combo_data = df[(df['test_case'] == test_case) & 
                               (df['jailbreak_tactic'] == tactic) & 
                               (df['turn_type'] == turn_type)]
                
                if len(combo_data) == 0:
                    continue
                    
                # Original ASR
                original_successes = combo_data['goal_achieved'].sum()
                total_experiments = len(combo_data)
                original_asr = (original_successes / total_experiments) * 100 if total_experiments > 0 else 0
                
                # Adjusted ASR
                # Only count FP among successful attacks
                successful_combo_data = combo_data[combo_data['goal_achieved'] == True]
                fp_mask = successful_combo_data['fp_decision'] == 'false_positive'
                fp_count = fp_mask.sum()
                adjusted_successes = original_successes - fp_count
                adjusted_asr = (adjusted_successes / total_experiments) * 100 if total_experiments > 0 else 0
                
                results.append({
                    'combination': f"{test_case} + {tactic} ({turn_type})",
                    'test_case': test_case,
                    'jailbreak_tactic': tactic,
                    'turn_type': turn_type,
                    'total_experiments': total_experiments,
                    'original_successes': original_successes,
                    'original_asr': original_asr,
                    'false_positives': fp_count,
                    'adjusted_successes': adjusted_successes,
                    'adjusted_asr': adjusted_asr,
                    'asr_difference': original_asr - adjusted_asr
                })
    
    return pd.DataFrame(results).sort_values(['original_asr', 'turn_type'], ascending=[False, True])

def create_comparison_plot(df, title, x_col, category_name):
    """Create side-by-side comparison plot for any dimension, with single/multi grouped by category."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Original ASR (Before FP Removal)', 'Adjusted ASR (After FP Removal)'),
        specs=[[{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Get unique categories and create grouped x-axis positions
    categories = df[x_col].unique()
    x_positions = []
    x_labels = []
    category_data = {'single': [], 'multi': []}
    
    # Group data by category, with single/multi side by side
    for i, category in enumerate(categories):
        cat_data = df[df[x_col] == category]
        
        # Add positions for single and multi-turn (side by side)
        base_pos = i * 3  # Space between category groups
        
        for turn_type in ['single', 'multi']:
            turn_data = cat_data[cat_data['turn_type'] == turn_type]
            if len(turn_data) > 0:
                pos = base_pos + (0 if turn_type == 'single' else 1)
                x_positions.append(pos)
                x_labels.append(f"{category}\n({turn_type})")
                category_data[turn_type].append({
                    'x_pos': pos,
                    'label': f"{category} ({turn_type})",
                    'category': category,
                    'original_asr': turn_data['original_asr'].iloc[0],
                    'adjusted_asr': turn_data['adjusted_asr'].iloc[0],
                    'original_successes': turn_data['original_successes'].iloc[0],
                    'adjusted_successes': turn_data['adjusted_successes'].iloc[0],
                    'total_experiments': turn_data['total_experiments'].iloc[0],
                    'false_positives': turn_data['false_positives'].iloc[0]
                })
    
    # Color mapping for turn types
    colors = {'single': ['lightcoral', 'lightblue'], 'multi': ['darkred', 'darkblue']}
    
    # Left plot: Original ASR
    for turn_type in ['single', 'multi']:
        if category_data[turn_type]:
            data = category_data[turn_type]
            fig.add_trace(
                go.Bar(
                    name=f'Original ASR ({turn_type})',
                    x=[d['x_pos'] for d in data],
                    y=[d['original_asr'] for d in data],
                    text=[f"{d['original_asr']:.1f}%" for d in data],
                    textposition='auto',
                    marker_color=colors[turn_type][0],
                    opacity=0.8,
                    hovertemplate='<b>%{customdata[0]}</b><br>Original ASR: %{y:.1f}%<br>Successes: %{customdata[1]}/%{customdata[2]}<extra></extra>',
                    customdata=[[d['label'], d['original_successes'], d['total_experiments']] for d in data],
                    legendgroup=turn_type,
                    showlegend=True
                ),
                row=1, col=1
            )
    
    # Right plot: Adjusted ASR
    for turn_type in ['single', 'multi']:
        if category_data[turn_type]:
            data = category_data[turn_type]
            fig.add_trace(
                go.Bar(
                    name=f'Adjusted ASR ({turn_type})',
                    x=[d['x_pos'] for d in data],
                    y=[d['adjusted_asr'] for d in data],
                    text=[f"{d['adjusted_asr']:.1f}%" for d in data],
                    textposition='auto',
                    marker_color=colors[turn_type][1],
                    opacity=0.8,
                    hovertemplate='<b>%{customdata[0]}</b><br>Adjusted ASR: %{y:.1f}%<br>Successes: %{customdata[1]}/%{customdata[2]}<extra></extra>',
                    customdata=[[d['label'], d['adjusted_successes'], d['total_experiments']] for d in data],
                    legendgroup=turn_type,
                    showlegend=False
                ),
                row=1, col=2
            )
    
    # Add FP count as scatter plot on right subplot
    all_data = category_data['single'] + category_data['multi']
    if all_data:
        fig.add_trace(
            go.Scatter(
                name='False Positives',
                x=[d['x_pos'] for d in all_data],
                y=[d['false_positives'] for d in all_data],
                mode='markers+text',
                text=[d['false_positives'] for d in all_data],
                textposition='top center',
                marker=dict(size=12, color='red', symbol='diamond'),
                yaxis='y2',
                hovertemplate='<b>%{customdata}</b><br>False Positives: %{y}<extra></extra>',
                customdata=[d['label'] for d in all_data]
            ),
            row=1, col=2
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"{title}: Impact of False Positive Evaluation (Single vs Multi-turn)",
            x=0.5,
            font=dict(size=16)
        ),
        height=600,
        showlegend=True,
        hovermode='closest',
        barmode='group'
    )
    
    # Create custom tick labels for category groups
    if all_data:
        # Get category group positions for tick marks
        category_positions = []
        category_labels = []
        for i, category in enumerate(categories):
            base_pos = i * 3
            category_positions.append(base_pos + 0.5)  # Center between single and multi bars
            category_labels.append(category)
        
        # Update x-axes with custom ticks
        fig.update_xaxes(
            title_text=f"{category_name} (Single vs Multi-turn)",
            row=1, col=1,
            tickvals=category_positions,
            ticktext=category_labels,
            tickangle=45
        )
        fig.update_xaxes(
            title_text=f"{category_name} (Single vs Multi-turn)",
            row=1, col=2,
            tickvals=category_positions,
            ticktext=category_labels,
            tickangle=45
        )
    
    # Update y-axes
    fig.update_yaxes(title_text="Attack Success Rate (%)", row=1, col=1)
    fig.update_yaxes(title_text="Attack Success Rate (%)", row=1, col=2)
    fig.update_yaxes(title_text="False Positives Count", secondary_y=True, row=1, col=2)
    
    return fig

def create_heatmap_plot(combo_df):
    """Create heatmap for test case + tactic combinations, split by turn type."""
    # Create subplots for single and multi-turn
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Single-turn Original ASR (%)', 'Single-turn Adjusted ASR (%)',
                       'Multi-turn Original ASR (%)', 'Multi-turn Adjusted ASR (%)'),
        specs=[[{"type": "heatmap"}, {"type": "heatmap"}],
               [{"type": "heatmap"}, {"type": "heatmap"}]]
    )
    
    for i, turn_type in enumerate(['single', 'multi']):
        turn_data = combo_df[combo_df['turn_type'] == turn_type]
        
        if len(turn_data) > 0:
            # Pivot for heatmap
            heatmap_original = turn_data.pivot(index='test_case', columns='jailbreak_tactic', values='original_asr').fillna(0)
            heatmap_adjusted = turn_data.pivot(index='test_case', columns='jailbreak_tactic', values='adjusted_asr').fillna(0)
            
            row = i + 1
            
            # Original ASR heatmap
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_original.values,
                    x=heatmap_original.columns,
                    y=heatmap_original.index,
                    colorscale='Reds',
                    text=heatmap_original.values,
                    texttemplate="%{text:.1f}%",
                    hovertemplate=f'<b>%{{y}} + %{{x}} ({turn_type})</b><br>Original ASR: %{{z:.1f}}%<extra></extra>',
                    showscale=True if i == 0 else False,
                    colorbar=dict(x=0.45) if i == 0 else None
                ),
                row=row, col=1
            )
            
            # Adjusted ASR heatmap  
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_adjusted.values,
                    x=heatmap_adjusted.columns,
                    y=heatmap_adjusted.index,
                    colorscale='Blues',
                    text=heatmap_adjusted.values,
                    texttemplate="%{text:.1f}%",
                    hovertemplate=f'<b>%{{y}} + %{{x}} ({turn_type})</b><br>Adjusted ASR: %{{z:.1f}}%<extra></extra>',
                    showscale=True if i == 0 else False,
                    colorbar=dict(x=1.02) if i == 0 else None
                ),
                row=row, col=2
            )
    
    fig.update_layout(
        title=dict(
            text="ASR Heatmap: Test Case × Tactic Combinations (by Turn Type)",
            x=0.5,
            font=dict(size=16)
        ),
        height=800
    )
    
    # Update axes for all subplots
    for row in [1, 2]:
        fig.update_xaxes(title_text="Jailbreak Tactic", row=row, col=1)
        fig.update_xaxes(title_text="Jailbreak Tactic", row=row, col=2)
        fig.update_yaxes(title_text="Test Case", row=row, col=1)
        fig.update_yaxes(title_text="Test Case", row=row, col=2)
    
    return fig

def create_summary_metrics(df):
    """Create summary metrics for the dashboard."""
    total_experiments = len(df)
    successful_original = df['goal_achieved'].sum()
    # Only count FP among successful attacks
    successful_data = df[df['goal_achieved'] == True]
    fp_count = (successful_data['fp_decision'] == 'false_positive').sum()
    successful_adjusted = successful_original - fp_count
    
    original_asr = (successful_original / total_experiments) * 100
    adjusted_asr = (successful_adjusted / total_experiments) * 100
    asr_reduction = original_asr - adjusted_asr
    
    # FP rate among successful attacks
    fp_rate_among_successful = (fp_count / successful_original) * 100 if successful_original > 0 else 0
    
    return {
        'total_experiments': total_experiments,
        'successful_original': successful_original,
        'successful_adjusted': successful_adjusted,
        'fp_count': fp_count,
        'original_asr': original_asr,
        'adjusted_asr': adjusted_asr,
        'asr_reduction': asr_reduction,
        'fp_rate_among_successful': fp_rate_among_successful
    }

def main():
    st.set_page_config(page_title="Batch3A Analysis Dashboard", layout="wide")
    
    st.title("🎯 Batch3A Comprehensive Analysis Dashboard")
    st.markdown("Interactive analysis of jailbreak attack success rates with false positive evaluation impact")
    
    try:
        # Load data
        df = load_batch3a_data()
        
        # Clean model names for better display
        df['model_short'] = df['target_model'].str.split('/').str[-1]
        
        # Create summary metrics
        metrics = create_summary_metrics(df)
        
        # Display summary metrics
        st.subheader("📊 Overall Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Experiments", metrics['total_experiments'])
        with col2:
            st.metric("Original ASR", f"{metrics['original_asr']:.1f}%")
        with col3:
            st.metric("Adjusted ASR", f"{metrics['adjusted_asr']:.1f}%")
        with col4:
            st.metric("ASR Reduction", f"{metrics['asr_reduction']:.1f}pp")
        
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("Original Successes", metrics['successful_original'])
        with col6:
            st.metric("False Positives", metrics['fp_count'])
        with col7:
            st.metric("Adjusted Successes", metrics['successful_adjusted'])
        with col8:
            st.metric("FP Rate (among successes)", f"{metrics['fp_rate_among_successful']:.1f}%")
        
        st.markdown("---")
        
        # Calculate ASR by different dimensions
        model_asr = calculate_asr_by_dimension(df, 'model_short')
        test_case_asr = calculate_asr_by_dimension(df, 'test_case')
        tactic_asr = calculate_asr_by_dimension(df, 'jailbreak_tactic')
        combo_asr = calculate_asr_by_combination(df)
        
        # 1. ASR by Model
        st.subheader("🤖 ASR by Model")
        st.plotly_chart(create_comparison_plot(model_asr, "ASR by Model", "model_short", "Model"), use_container_width=True)
        
        with st.expander("📋 View Model ASR Data"):
            st.dataframe(
                model_asr.style.format({
                    'original_asr': '{:.1f}%',
                    'adjusted_asr': '{:.1f}%',
                    'asr_difference': '{:.1f}%'
                }),
                use_container_width=True
            )
        
        st.markdown("---")
        
        # 2. ASR by Test Case
        st.subheader("📝 ASR by Test Case")
        st.plotly_chart(create_comparison_plot(test_case_asr, "ASR by Test Case", "test_case", "Test Case"), use_container_width=True)
        
        with st.expander("📋 View Test Case ASR Data"):
            st.dataframe(
                test_case_asr.style.format({
                    'original_asr': '{:.1f}%',
                    'adjusted_asr': '{:.1f}%',
                    'asr_difference': '{:.1f}%'
                }),
                use_container_width=True
            )
        
        st.markdown("---")
        
        # 3. ASR by Tactic
        st.subheader("⚔️ ASR by Tactic")
        st.plotly_chart(create_comparison_plot(tactic_asr, "ASR by Tactic", "jailbreak_tactic", "Jailbreak Tactic"), use_container_width=True)
        
        with st.expander("📋 View Tactic ASR Data"):
            st.dataframe(
                tactic_asr.style.format({
                    'original_asr': '{:.1f}%',
                    'adjusted_asr': '{:.1f}%',
                    'asr_difference': '{:.1f}%'
                }),
                use_container_width=True
            )
        
        st.markdown("---")
        
        # 4. ASR by Test Case + Tactic Combination
        st.subheader("🎯 ASR by Test Case × Tactic Combinations")
        
        # Heatmap
        st.plotly_chart(create_heatmap_plot(combo_asr), use_container_width=True)
        
        # Top combinations table
        st.subheader("🏆 Top Performing Combinations")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original ASR (Top 10)**")
            top_original = combo_asr.nlargest(10, 'original_asr')[['combination', 'original_asr', 'total_experiments']]
            st.dataframe(
                top_original.style.format({'original_asr': '{:.1f}%'}),
                use_container_width=True
            )
        
        with col2:
            st.markdown("**Adjusted ASR (Top 10)**")
            top_adjusted = combo_asr.nlargest(10, 'adjusted_asr')[['combination', 'adjusted_asr', 'total_experiments']]
            st.dataframe(
                top_adjusted.style.format({'adjusted_asr': '{:.1f}%'}),
                use_container_width=True
            )
        
        # Most affected by FP
        st.subheader("📉 Combinations Most Affected by False Positives")
        most_affected = combo_asr.nlargest(10, 'asr_difference')[['combination', 'original_asr', 'adjusted_asr', 'asr_difference', 'false_positives']]
        st.dataframe(
            most_affected.style.format({
                'original_asr': '{:.1f}%',
                'adjusted_asr': '{:.1f}%',
                'asr_difference': '{:.1f}%'
            }),
            use_container_width=True
        )
        
        # Full combination data
        with st.expander("📋 View All Combination Data"):
            st.dataframe(
                combo_asr.style.format({
                    'original_asr': '{:.1f}%',
                    'adjusted_asr': '{:.1f}%',
                    'asr_difference': '{:.1f}%'
                }),
                use_container_width=True
            )
            
    except FileNotFoundError:
        st.error("❌ Batch3A CSV file not found. Make sure batch3A_results.csv exists in csv_results/")
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")

if __name__ == "__main__":
    main()