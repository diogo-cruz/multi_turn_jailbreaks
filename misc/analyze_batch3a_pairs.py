#!/usr/bin/env python3
"""
Batch3A Paired Evaluations Analysis

This script analyzes the 108 paired evaluations in batch3A where identical experimental
conditions were evaluated by both GPT-4o-mini and GPT-4.1-nano evaluators.

It performs:
1. Direct analysis of raw JSONL files to extract scores
2. Statistical comparison between evaluators
3. Factor importance analysis (test case, model, tactic, evaluator)
4. Multi-turn analysis with separate stages
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

def read_jsonl_scores(file_path):
    """Extract scores from JSONL file, separating by round for multi-turn"""
    try:
        with open(file_path, 'r') as f:
            data = []
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    data.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Extract scores by round
        scores_by_round = {}
        max_score = float('-inf')  # Allow negative scores
        goal_achieved = False
        
        for entry in data:
            if 'score' in entry and entry['score'] != 'refused':
                try:
                    score = float(entry['score'])
                    round_num = entry.get('round', 1)
                    scores_by_round[round_num] = score
                    max_score = max(max_score, score)
                except (ValueError, TypeError):
                    pass
            
            if entry.get('goal_achieved'):
                goal_achieved = True
        
        # If no scores found, return 0.0 as max_score
        if max_score == float('-inf'):
            max_score = 0.0
        
        return scores_by_round, max_score, goal_achieved
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}, 0.0, False

def find_paired_evaluations():
    """Find all paired evaluations in batch3A"""
    batch3a_dir = Path('../clean_results/final_runs/batch3A/crowding')
    
    if not batch3a_dir.exists():
        print(f"Directory {batch3a_dir} not found")
        return []
    
    # Find all JSONL files
    all_files = list(batch3a_dir.glob('*.jsonl'))
    
    # Group by base condition (everything before _eval_)
    base_conditions = {}
    for file_path in all_files:
        filename = file_path.name
        if '_eval_' in filename:
            base_condition = filename.split('_eval_')[0]
            evaluator = filename.split('_eval_')[1].replace('.jsonl', '')
            
            if base_condition not in base_conditions:
                base_conditions[base_condition] = {}
            base_conditions[base_condition][evaluator] = file_path
    
    # Find pairs with both evaluators
    paired_conditions = []
    for base_condition, evaluators in base_conditions.items():
        if 'gpt-4o-mini' in evaluators and 'gpt-4.1-nano' in evaluators:
            paired_conditions.append({
                'base_condition': base_condition,
                'gpt4o_mini_file': evaluators['gpt-4o-mini'],
                'gpt41_nano_file': evaluators['gpt-4.1-nano']
            })
    
    return paired_conditions

def extract_experimental_factors(base_condition):
    """Extract tactic, test_case, target_model, turn_type from base condition"""
    parts = base_condition.split('_')
    
    if len(parts) < 4:
        return None, None, None, None
    
    tactic = parts[0]
    test_case = parts[1]
    
    # Find target model (look for known model patterns)
    model_patterns = ['gpt', 'claude', 'llama', 'deepseek', 'gemini']
    target_model = None
    turn_type = None
    
    for i, part in enumerate(parts):
        if any(pattern in part.lower() for pattern in model_patterns):
            # Reconstruct model name (might be split by underscores)
            model_parts = [part]
            j = i + 1
            while j < len(parts) and not any(x in parts[j] for x in ['single', 'multi', 'sample']):
                model_parts.append(parts[j])
                j += 1
            target_model = '-'.join(model_parts)
            break
    
    # Find turn type
    if 'single' in base_condition:
        turn_type = 'single'
    elif 'multi' in base_condition:
        turn_type = 'multi'
    
    return tactic, test_case, target_model, turn_type

def analyze_paired_evaluations():
    """Main analysis function"""
    print("Finding paired evaluations in batch3A...")
    paired_conditions = find_paired_evaluations()
    
    print(f"Found {len(paired_conditions)} paired evaluations")
    
    if len(paired_conditions) == 0:
        print("No paired evaluations found. Check directory structure.")
        return
    
    # Analyze each pair
    results = []
    
    for pair in paired_conditions:
        base_condition = pair['base_condition']
        
        # Extract experimental factors
        tactic, test_case, target_model, turn_type = extract_experimental_factors(base_condition)
        
        if not all([tactic, test_case, target_model, turn_type]):
            print(f"Could not parse: {base_condition}")
            continue
        
        # Read scores from both files
        gpt4o_scores, gpt4o_max, gpt4o_goal = read_jsonl_scores(pair['gpt4o_mini_file'])
        gpt41_scores, gpt41_max, gpt41_goal = read_jsonl_scores(pair['gpt41_nano_file'])
        
        # Create result record
        result = {
            'base_condition': base_condition,
            'tactic': tactic,
            'test_case': test_case,
            'target_model': target_model,
            'turn_type': turn_type,
            'gpt4o_mini_max_score': gpt4o_max,
            'gpt41_nano_max_score': gpt41_max,
            'gpt4o_mini_goal_achieved': gpt4o_goal,
            'gpt41_nano_goal_achieved': gpt41_goal,
            'score_difference': gpt4o_max - gpt41_max,
            'goal_difference': int(gpt4o_goal) - int(gpt41_goal)
        }
        
        # Add round-by-round scores for multi-turn
        if turn_type == 'multi':
            gpt4o_max_round = max(gpt4o_scores.keys()) if gpt4o_scores else 0
            gpt41_max_round = max(gpt41_scores.keys()) if gpt41_scores else 0
            max_rounds = max(gpt4o_max_round, gpt41_max_round)
            
            for round_num in range(1, max_rounds + 1):
                gpt4o_round_score = gpt4o_scores.get(round_num, 0.0)
                gpt41_round_score = gpt41_scores.get(round_num, 0.0)
                
                result[f'gpt4o_mini_round_{round_num}'] = gpt4o_round_score
                result[f'gpt41_nano_round_{round_num}'] = gpt41_round_score
                result[f'round_{round_num}_difference'] = gpt4o_round_score - gpt41_round_score
        
        results.append(result)
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    print(f"Successfully analyzed {len(df)} paired evaluations")
    
    return df

def statistical_analysis(df):
    """Perform statistical analysis of evaluator differences"""
    print("\n" + "="*50)
    print("STATISTICAL ANALYSIS OF EVALUATOR DIFFERENCES")
    print("="*50)
    
    # Basic statistics
    gpt4o_scores = df['gpt4o_mini_max_score']
    gpt41_scores = df['gpt41_nano_max_score']
    
    print(f"\nBasic Statistics:")
    print(f"GPT-4o-mini mean score: {gpt4o_scores.mean():.3f} (std: {gpt4o_scores.std():.3f})")
    print(f"GPT-4.1-nano mean score: {gpt41_scores.mean():.3f} (std: {gpt41_scores.std():.3f})")
    print(f"Mean difference (GPT-4o-mini - GPT-4.1-nano): {df['score_difference'].mean():.3f}")
    
    # Paired t-test
    t_stat, p_value = stats.ttest_rel(gpt4o_scores, gpt41_scores)
    print(f"\nPaired t-test:")
    print(f"t-statistic: {t_stat:.3f}")
    print(f"p-value: {p_value:.6f}")
    print(f"Significant difference: {'Yes' if p_value < 0.05 else 'No'}")
    
    # Effect size (Cohen's d for paired samples)
    diff_scores = gpt4o_scores - gpt41_scores
    cohens_d = diff_scores.mean() / diff_scores.std() if diff_scores.std() > 0 else 0
    print(f"Effect size (Cohen's d): {cohens_d:.3f}")
    
    # Correlation
    correlation, corr_p = stats.pearsonr(gpt4o_scores, gpt41_scores)
    print(f"\nCorrelation between evaluators:")
    print(f"Pearson r: {correlation:.3f} (p={corr_p:.6f})")
    
    # Goal achievement comparison
    gpt4o_goals = df['gpt4o_mini_goal_achieved'].astype(int)
    gpt41_goals = df['gpt41_nano_goal_achieved'].astype(int)
    
    print(f"\nGoal Achievement:")
    print(f"GPT-4o-mini success rate: {gpt4o_goals.mean():.3f}")
    print(f"GPT-4.1-nano success rate: {gpt41_goals.mean():.3f}")
    
    # Goal achievement contingency analysis
    both_success = ((gpt4o_goals == 1) & (gpt41_goals == 1)).sum()
    gpt4o_only = ((gpt4o_goals == 1) & (gpt41_goals == 0)).sum()
    gpt41_only = ((gpt4o_goals == 0) & (gpt41_goals == 1)).sum()
    both_fail = ((gpt4o_goals == 0) & (gpt41_goals == 0)).sum()
    
    print(f"Both succeed: {both_success}, GPT-4o-mini only: {gpt4o_only}")
    print(f"GPT-4.1-nano only: {gpt41_only}, Both fail: {both_fail}")
    
    # Chi-square test for independence (only if valid contingency table)
    if gpt4o_only + gpt41_only > 0 and both_success + both_fail > 0:
        try:
            chi2, chi2_p = stats.chi2_contingency([[both_success, gpt4o_only], [gpt41_only, both_fail]])[:2]
            print(f"Chi-square test p-value: {chi2_p:.6f}")
        except ValueError:
            print("Chi-square test not applicable (insufficient variation)")

def factor_importance_analysis(df):
    """Analyze which factors are most important for determining scores"""
    print("\n" + "="*50)
    print("FACTOR IMPORTANCE ANALYSIS")
    print("="*50)
    
    # Prepare data for analysis
    analysis_df = df.copy()
    
    # Add evaluator as a factor by creating long format
    long_data = []
    for _, row in analysis_df.iterrows():
        # GPT-4o-mini record
        long_data.append({
            'tactic': row['tactic'],
            'test_case': row['test_case'],
            'target_model': row['target_model'],
            'turn_type': row['turn_type'],
            'evaluator': 'GPT-4o-mini',
            'score': row['gpt4o_mini_max_score'],
            'goal_achieved': row['gpt4o_mini_goal_achieved']
        })
        
        # GPT-4.1-nano record
        long_data.append({
            'tactic': row['tactic'],
            'test_case': row['test_case'],
            'target_model': row['target_model'],
            'turn_type': row['turn_type'],
            'evaluator': 'GPT-4.1-nano',
            'score': row['gpt41_nano_max_score'],
            'goal_achieved': row['gpt41_nano_goal_achieved']
        })
    
    long_df = pd.DataFrame(long_data)
    
    # Random Forest analysis
    print("\n1. Random Forest Feature Importance:")
    
    # Encode categorical variables
    encoders = {}
    encoded_features = []
    feature_names = ['tactic', 'test_case', 'target_model', 'turn_type', 'evaluator']
    
    for feature in feature_names:
        encoder = LabelEncoder()
        encoded_col = encoder.fit_transform(long_df[feature])
        encoded_features.append(encoded_col)
        encoders[feature] = encoder
    
    X = np.column_stack(encoded_features)
    y = long_df['score'].values
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    importance_scores = rf.feature_importances_
    for i, feature in enumerate(feature_names):
        print(f"  {feature}: {importance_scores[i]:.3f}")
    
    # ANOVA analysis
    print("\n2. ANOVA F-statistics:")
    
    for feature in feature_names:
        groups = [long_df[long_df[feature] == group]['score'].values 
                 for group in long_df[feature].unique()]
        f_stat, p_val = stats.f_oneway(*[g for g in groups if len(g) > 0])
        print(f"  {feature}: F={f_stat:.3f}, p={p_val:.6f}")
    
    return long_df

def multiturn_stage_analysis(df):
    """Analyze multi-turn experiments by individual rounds"""
    print("\n" + "="*50)
    print("MULTI-TURN STAGE ANALYSIS")
    print("="*50)
    
    # Filter for multi-turn experiments
    multi_df = df[df['turn_type'] == 'multi'].copy()
    
    if len(multi_df) == 0:
        print("No multi-turn experiments found")
        return
    
    print(f"Analyzing {len(multi_df)} multi-turn experiments")
    
    # Find maximum number of rounds
    round_cols_gpt4o = [col for col in multi_df.columns if col.startswith('gpt4o_mini_round_')]
    round_cols_gpt41 = [col for col in multi_df.columns if col.startswith('gpt41_nano_round_')]
    
    if not round_cols_gpt4o:
        print("No round-by-round data found")
        return
    
    max_rounds = len(round_cols_gpt4o)
    print(f"Maximum rounds found: {max_rounds}")
    
    # Analyze each round
    round_analysis = []
    
    for round_num in range(1, max_rounds + 1):
        gpt4o_col = f'gpt4o_mini_round_{round_num}'
        gpt41_col = f'gpt41_nano_round_{round_num}'
        diff_col = f'round_{round_num}_difference'
        
        if gpt4o_col in multi_df.columns and gpt41_col in multi_df.columns:
            gpt4o_scores = multi_df[gpt4o_col]
            gpt41_scores = multi_df[gpt41_col]
            
            # Remove zero scores (rounds that didn't occur)
            valid_mask = (gpt4o_scores > 0) | (gpt41_scores > 0)
            if valid_mask.sum() == 0:
                continue
                
            gpt4o_valid = gpt4o_scores[valid_mask]
            gpt41_valid = gpt41_scores[valid_mask]
            
            if len(gpt4o_valid) < 2:
                continue
            
            # Statistical analysis for this round
            t_stat, p_val = stats.ttest_rel(gpt4o_valid, gpt41_valid)
            correlation, _ = stats.pearsonr(gpt4o_valid, gpt41_valid)
            
            round_analysis.append({
                'round': round_num,
                'n_experiments': len(gpt4o_valid),
                'gpt4o_mean': gpt4o_valid.mean(),
                'gpt41_mean': gpt41_valid.mean(),
                'mean_difference': (gpt4o_valid - gpt41_valid).mean(),
                't_statistic': t_stat,
                'p_value': p_val,
                'correlation': correlation
            })
    
    # Display round analysis
    round_df = pd.DataFrame(round_analysis)
    
    if len(round_df) > 0:
        print("\nRound-by-round analysis:")
        print(round_df.to_string(index=False, float_format='%.3f'))
        
        # Plot round progression
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.plot(round_df['round'], round_df['gpt4o_mean'], 'o-', label='GPT-4o-mini', color='red')
        plt.plot(round_df['round'], round_df['gpt41_mean'], 's-', label='GPT-4.1-nano', color='blue')
        plt.xlabel('Round')
        plt.ylabel('Mean Score')
        plt.title('Score Progression by Round')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 2)
        plt.plot(round_df['round'], round_df['mean_difference'], 'o-', color='green')
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.xlabel('Round')
        plt.ylabel('Score Difference (GPT-4o-mini - GPT-4.1-nano)')
        plt.title('Evaluator Difference by Round')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 3)
        plt.plot(round_df['round'], round_df['correlation'], 'o-', color='purple')
        plt.xlabel('Round')
        plt.ylabel('Correlation between Evaluators')
        plt.title('Evaluator Correlation by Round')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 4)
        significant = round_df['p_value'] < 0.05
        colors = ['red' if sig else 'gray' for sig in significant]
        plt.bar(round_df['round'], -np.log10(round_df['p_value']), color=colors)
        plt.axhline(y=-np.log10(0.05), color='red', linestyle='--', label='p=0.05')
        plt.xlabel('Round')
        plt.ylabel('-log10(p-value)')
        plt.title('Statistical Significance by Round')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('batch3a_multiturn_analysis.png', dpi=300, bbox_inches='tight')
        print(f"\nMulti-turn analysis plot saved as 'batch3a_multiturn_analysis.png'")

def create_visualizations(df, long_df):
    """Create comprehensive visualizations"""
    print("\n" + "="*50)
    print("CREATING VISUALIZATIONS")
    print("="*50)
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Score comparison scatter plot
    ax = axes[0, 0]
    ax.scatter(df['gpt41_nano_max_score'], df['gpt4o_mini_max_score'], alpha=0.6, s=50)
    max_score = max(df['gpt41_nano_max_score'].max(), df['gpt4o_mini_max_score'].max())
    ax.plot([0, max_score], [0, max_score], 'r--', alpha=0.5, label='Perfect Agreement')
    ax.set_xlabel('GPT-4.1-nano Score')
    ax.set_ylabel('GPT-4o-mini Score')
    ax.set_title('Evaluator Score Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Score differences by test case
    ax = axes[0, 1]
    test_case_diffs = df.groupby('test_case')['score_difference'].mean().sort_values()
    bars = ax.bar(range(len(test_case_diffs)), test_case_diffs.values)
    ax.set_xticks(range(len(test_case_diffs)))
    ax.set_xticklabels(test_case_diffs.index, rotation=45, ha='right')
    ax.set_ylabel('Mean Score Difference (GPT-4o-mini - GPT-4.1-nano)')
    ax.set_title('Evaluator Bias by Test Case')
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax.grid(True, alpha=0.3)
    
    # Color bars based on positive/negative
    for i, bar in enumerate(bars):
        if test_case_diffs.values[i] > 0:
            bar.set_color('red')
        else:
            bar.set_color('blue')
    
    # 3. Score differences by target model
    ax = axes[0, 2]
    model_diffs = df.groupby('target_model')['score_difference'].mean().sort_values()
    bars = ax.bar(range(len(model_diffs)), model_diffs.values)
    ax.set_xticks(range(len(model_diffs)))
    ax.set_xticklabels(model_diffs.index, rotation=45, ha='right')
    ax.set_ylabel('Mean Score Difference')
    ax.set_title('Evaluator Bias by Target Model')
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax.grid(True, alpha=0.3)
    
    for i, bar in enumerate(bars):
        if model_diffs.values[i] > 0:
            bar.set_color('red')
        else:
            bar.set_color('blue')
    
    # 4. Distribution of scores by evaluator
    ax = axes[1, 0]
    ax.hist(df['gpt4o_mini_max_score'], alpha=0.5, bins=20, label='GPT-4o-mini', color='red', density=True)
    ax.hist(df['gpt41_nano_max_score'], alpha=0.5, bins=20, label='GPT-4.1-nano', color='blue', density=True)
    ax.set_xlabel('Score')
    ax.set_ylabel('Density')
    ax.set_title('Score Distribution by Evaluator')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 5. Turn type comparison
    ax = axes[1, 1]
    turn_comparison = df.groupby('turn_type').agg({
        'gpt4o_mini_max_score': 'mean',
        'gpt41_nano_max_score': 'mean'
    })
    
    x = np.arange(len(turn_comparison.index))
    width = 0.35
    
    ax.bar(x - width/2, turn_comparison['gpt4o_mini_max_score'], width, 
           label='GPT-4o-mini', color='red', alpha=0.7)
    ax.bar(x + width/2, turn_comparison['gpt41_nano_max_score'], width,
           label='GPT-4.1-nano', color='blue', alpha=0.7)
    
    ax.set_xlabel('Turn Type')
    ax.set_ylabel('Mean Score')
    ax.set_title('Mean Scores by Turn Type')
    ax.set_xticks(x)
    ax.set_xticklabels(turn_comparison.index)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 6. Score difference distribution
    ax = axes[1, 2]
    ax.hist(df['score_difference'], bins=20, alpha=0.7, color='green', edgecolor='black')
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No Difference')
    ax.axvline(x=df['score_difference'].mean(), color='orange', linestyle='-', linewidth=2, 
               label=f'Mean Diff: {df["score_difference"].mean():.3f}')
    ax.set_xlabel('Score Difference (GPT-4o-mini - GPT-4.1-nano)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Score Differences')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('batch3a_evaluator_analysis.png', dpi=300, bbox_inches='tight')
    print("Main analysis plot saved as 'batch3a_evaluator_analysis.png'")

def main():
    """Main execution function"""
    print("Batch3A Paired Evaluations Analysis")
    print("=" * 50)
    
    # Analyze paired evaluations
    df = analyze_paired_evaluations()
    
    if df is None or len(df) == 0:
        print("No data to analyze")
        return
    
    # Save raw results
    df.to_csv('batch3a_paired_results.csv', index=False)
    print(f"Raw results saved to 'batch3a_paired_results.csv'")
    
    # Statistical analysis
    statistical_analysis(df)
    
    # Factor importance analysis
    long_df = factor_importance_analysis(df)
    
    # Multi-turn stage analysis
    multiturn_stage_analysis(df)
    
    # Create visualizations
    create_visualizations(df, long_df)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print("Files generated:")
    print("- batch3a_paired_results.csv: Raw analysis results")
    print("- batch3a_evaluator_analysis.png: Main analysis plots")
    print("- batch3a_multiturn_analysis.png: Multi-turn round analysis")

if __name__ == "__main__":
    main()