#!/usr/bin/env python3
"""
Qualitative analysis of tactics and test cases using PCA and UMAP.
Creates scatter plots to identify patterns and clusters in the data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Try to import UMAP, fall back to just PCA if not available
try:
    from umap import UMAP
    UMAP_AVAILABLE = True
except ImportError:
    print("UMAP not available, using only PCA")
    UMAP_AVAILABLE = False

# Set up matplotlib
plt.rcParams.update({
    'text.usetex': False,
    'font.family': 'serif',
    'font.size': 12
})

def filter_and_prepare_data(df):
    """
    Filter data according to specifications:
    - Temperature 0
    - GPT-4o-mini as attacker and evaluator
    - Ignore data where reasoning is filled but not none
    """
    # Filter for temperature 0
    df_filtered = df[df['target_temp'] == 0.0].copy()
    
    # Filter for GPT-4o-mini as both attacker and evaluator
    df_filtered = df_filtered[
        (df_filtered['attacker_model'] == 'openai/gpt-4o-mini-2024-07-18') &
        (df_filtered['evaluator_model'] == 'openai/gpt-4o-mini')
    ].copy()
    
    # Filter out data where reasoning is filled but not 'none'
    df_filtered = df_filtered[
        (df_filtered['reasoning'].isna()) |
        (df_filtered['reasoning'] == 'none') |
        (df_filtered['reasoning'] == '')
    ].copy()
    
    print(f"After filtering: {len(df_filtered)} records remaining")
    return df_filtered

def create_feature_vectors(df, variant='tactic_testcase'):
    """
    Create numerical feature vectors for each row.
    
    variant: 'tactic_testcase' or 'model_focused'
    """
    # Create label encoders for categorical variables
    encoders = {}
    
    if variant == 'tactic_testcase':
        # Keep model, compress other dimensions
        categorical_cols = ['target_model', 'jailbreak_tactic', 'test_case']
        preserve_cols = ['turn_type', 'jailbreak_tactic', 'test_case']
    else:  # model_focused
        # Keep tactic and test case, compress models
        categorical_cols = ['target_model', 'jailbreak_tactic', 'test_case']
        preserve_cols = ['turn_type', 'target_model']
    
    feature_data = []
    preserve_data = []
    
    for _, row in df.iterrows():
        features = []
        
        # Add categorical features as one-hot encoded
        for col in categorical_cols:
            if col not in encoders:
                unique_vals = df[col].unique()
                encoders[col] = {val: i for i, val in enumerate(unique_vals)}
            
            # One-hot encode
            one_hot = [0] * len(encoders[col])
            if row[col] in encoders[col]:
                one_hot[encoders[col][row[col]]] = 1
            features.extend(one_hot)
        
        # Add numerical features
        features.extend([
            row['goal_achieved'],
            row['refused'],
            row['max_round'] if not pd.isna(row['max_round']) else 0,
            1 if row['turn_type'] == 'multi' else 0,
        ])
        
        # Parse scores if available
        if pd.notna(row['scores']) and row['scores'] != '[]':
            try:
                # Parse the scores string (assuming it's a list representation)
                scores_str = row['scores'].strip('[]')
                if scores_str:
                    scores = [float(x.strip()) for x in scores_str.split(',')]
                    features.append(np.mean(scores))
                    features.append(np.std(scores) if len(scores) > 1 else 0)
                else:
                    features.extend([0, 0])
            except:
                features.extend([0, 0])
        else:
            features.extend([0, 0])
        
        feature_data.append(features)
        
        # Preserve information for coloring/labeling
        preserve_info = {}
        for col in preserve_cols:
            preserve_info[col] = row[col]
        preserve_data.append(preserve_info)
    
    return np.array(feature_data), preserve_data, encoders

def create_pca_plot(features, preserve_data, variant, n_components=2):
    """
    Create PCA scatter plot
    """
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    features_pca = pca.fit_transform(features_scaled)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if variant == 'tactic_testcase':
        # Color by tactic, shape by turn type
        tactics = list(set([p['jailbreak_tactic'] for p in preserve_data]))
        colors = plt.cm.tab10(np.linspace(0, 1, len(tactics)))
        tactic_colors = {tactic: colors[i] for i, tactic in enumerate(tactics)}
        
        for turn_type in ['single', 'multi']:
            mask = np.array([p['turn_type'] == turn_type for p in preserve_data])
            if np.any(mask):
                for tactic in tactics:
                    tactic_mask = mask & np.array([p['jailbreak_tactic'] == tactic for p in preserve_data])
                    if np.any(tactic_mask):
                        marker = 'o' if turn_type == 'single' else 's'
                        ax.scatter(features_pca[tactic_mask, 0], features_pca[tactic_mask, 1],
                                 c=[tactic_colors[tactic]], marker=marker, s=50, alpha=0.7,
                                 label=f"{tactic.replace('_', ' ').title()} ({turn_type})")
        
        title = 'PCA: Tactics and Test Cases\n(Colors=Tactics, Shapes=Turn Type)'
        
    else:  # model_focused
        # Color by turn type, different models as different shapes
        models = list(set([p['target_model'] for p in preserve_data]))
        # Use only a subset of models for readability
        top_models = models[:8] if len(models) > 8 else models
        
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p']
        model_markers = {model: markers[i % len(markers)] for i, model in enumerate(top_models)}
        
        for turn_type, color in [('single', 'blue'), ('multi', 'red')]:
            for model in top_models:
                mask = np.array([p['turn_type'] == turn_type and p['target_model'] == model 
                               for p in preserve_data])
                if np.any(mask):
                    model_short = model.split('/')[-1] if '/' in model else model
                    model_short = model_short[:15] + "..." if len(model_short) > 15 else model_short
                    ax.scatter(features_pca[mask, 0], features_pca[mask, 1],
                             c=color, marker=model_markers[model], s=50, alpha=0.7,
                             label=f"{model_short} ({turn_type})")
        
        title = 'PCA: Models and Turn Types\n(Colors=Turn Type, Shapes=Models)'
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig, pca

def create_umap_plot(features, preserve_data, variant):
    """
    Create UMAP scatter plot
    """
    if not UMAP_AVAILABLE:
        print("UMAP not available, skipping UMAP plot")
        return None
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply UMAP
    reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    features_umap = reducer.fit_transform(features_scaled)
    
    # Create plot (similar to PCA plot)
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if variant == 'tactic_testcase':
        # Color by tactic, shape by turn type
        tactics = list(set([p['jailbreak_tactic'] for p in preserve_data]))
        colors = plt.cm.tab10(np.linspace(0, 1, len(tactics)))
        tactic_colors = {tactic: colors[i] for i, tactic in enumerate(tactics)}
        
        for turn_type in ['single', 'multi']:
            mask = np.array([p['turn_type'] == turn_type for p in preserve_data])
            if np.any(mask):
                for tactic in tactics:
                    tactic_mask = mask & np.array([p['jailbreak_tactic'] == tactic for p in preserve_data])
                    if np.any(tactic_mask):
                        marker = 'o' if turn_type == 'single' else 's'
                        ax.scatter(features_umap[tactic_mask, 0], features_umap[tactic_mask, 1],
                                 c=[tactic_colors[tactic]], marker=marker, s=50, alpha=0.7,
                                 label=f"{tactic.replace('_', ' ').title()} ({turn_type})")
        
        title = 'UMAP: Tactics and Test Cases\n(Colors=Tactics, Shapes=Turn Type)'
        
    else:  # model_focused
        # Color by turn type, different models as different shapes
        models = list(set([p['target_model'] for p in preserve_data]))
        top_models = models[:8] if len(models) > 8 else models
        
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p']
        model_markers = {model: markers[i % len(markers)] for i, model in enumerate(top_models)}
        
        for turn_type, color in [('single', 'blue'), ('multi', 'red')]:
            for model in top_models:
                mask = np.array([p['turn_type'] == turn_type and p['target_model'] == model 
                               for p in preserve_data])
                if np.any(mask):
                    model_short = model.split('/')[-1] if '/' in model else model
                    model_short = model_short[:15] + "..." if len(model_short) > 15 else model_short
                    ax.scatter(features_umap[mask, 0], features_umap[mask, 1],
                             c=color, marker=model_markers[model], s=50, alpha=0.7,
                             label=f"{model_short} ({turn_type})")
        
        title = 'UMAP: Models and Turn Types\n(Colors=Turn Type, Shapes=Models)'
    
    ax.set_xlabel('UMAP 1')
    ax.set_ylabel('UMAP 2')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def main():
    # Load data
    print("Loading data...")
    df = pd.read_csv('../../csv_results/master_results.csv')
    print(f"Total records: {len(df)}")
    
    # Filter and prepare data
    df_filtered = filter_and_prepare_data(df)
    
    if len(df_filtered) == 0:
        print("No data remaining after filtering!")
        return
    
    # Create output directory
    output_dir = Path('../plots')
    output_dir.mkdir(exist_ok=True)
    
    # Variant 1: Focus on tactics and test cases
    print("Creating feature vectors for tactic/test case analysis...")
    features1, preserve_data1, encoders1 = create_feature_vectors(df_filtered, 'tactic_testcase')
    
    print(f"Feature matrix shape: {features1.shape}")
    
    print("Creating PCA plot for tactic/test case analysis...")
    fig1, pca1 = create_pca_plot(features1, preserve_data1, 'tactic_testcase')
    fig1.savefig(output_dir / 'qualitative_pca_tactics.pdf', dpi=300, bbox_inches='tight')
    fig1.savefig(output_dir / 'qualitative_pca_tactics.png', dpi=300, bbox_inches='tight')
    print(f"PCA plot (tactics) saved to {output_dir / 'qualitative_pca_tactics.pdf'}")
    
    if UMAP_AVAILABLE:
        print("Creating UMAP plot for tactic/test case analysis...")
        fig2 = create_umap_plot(features1, preserve_data1, 'tactic_testcase')
        if fig2:
            fig2.savefig(output_dir / 'qualitative_umap_tactics.pdf', dpi=300, bbox_inches='tight')
            fig2.savefig(output_dir / 'qualitative_umap_tactics.png', dpi=300, bbox_inches='tight')
            print(f"UMAP plot (tactics) saved to {output_dir / 'qualitative_umap_tactics.pdf'}")
    
    # Variant 2: Focus on models
    print("Creating feature vectors for model analysis...")
    features2, preserve_data2, encoders2 = create_feature_vectors(df_filtered, 'model_focused')
    
    print("Creating PCA plot for model analysis...")
    fig3, pca2 = create_pca_plot(features2, preserve_data2, 'model_focused')
    fig3.savefig(output_dir / 'qualitative_pca_models.pdf', dpi=300, bbox_inches='tight')
    fig3.savefig(output_dir / 'qualitative_pca_models.png', dpi=300, bbox_inches='tight')
    print(f"PCA plot (models) saved to {output_dir / 'qualitative_pca_models.pdf'}")
    
    if UMAP_AVAILABLE:
        print("Creating UMAP plot for model analysis...")
        fig4 = create_umap_plot(features2, preserve_data2, 'model_focused')
        if fig4:
            fig4.savefig(output_dir / 'qualitative_umap_models.pdf', dpi=300, bbox_inches='tight')
            fig4.savefig(output_dir / 'qualitative_umap_models.png', dpi=300, bbox_inches='tight')
            print(f"UMAP plot (models) saved to {output_dir / 'qualitative_umap_models.pdf'}")
    
    # Print summary information
    print("\nSummary Information:")
    print("===================")
    print(f"PCA explained variance (tactics): {pca1.explained_variance_ratio_[:2]}")
    print(f"Total explained variance: {pca1.explained_variance_ratio_[:2].sum():.3f}")
    
    print(f"\nPCA explained variance (models): {pca2.explained_variance_ratio_[:2]}")
    print(f"Total explained variance: {pca2.explained_variance_ratio_[:2].sum():.3f}")
    
    print(f"\nData distribution:")
    tactics = df_filtered['jailbreak_tactic'].value_counts()
    print("Tactics:")
    for tactic, count in tactics.items():
        print(f"  {tactic}: {count}")
    
    test_cases = df_filtered['test_case'].value_counts()
    print("\nTest cases:")
    for test_case, count in test_cases.head(10).items():
        print(f"  {test_case}: {count}")
    
    models = df_filtered['target_model'].value_counts()
    print(f"\nNumber of models: {len(models)}")
    print("Top 10 models:")
    for model, count in models.head(10).items():
        model_short = model.split('/')[-1] if '/' in model else model
        print(f"  {model_short}: {count}")
    
    plt.show()

if __name__ == '__main__':
    main() 