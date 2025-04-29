"""
Jailbreak Attack Results Merged Data Analysis

This script provides analytical capabilities for processing and deriving insights from
merged jailbreak attack result datasets. It works with consolidated data that combines
results from multiple attack runs, tactics, and model configurations to identify broader
patterns and relationships.

Key features:
- Statistical analysis of merged attack result data
- Identification of trends across multiple experiment dimensions
- Calculation of aggregate metrics such as attack success rates
- Correlation analysis between model properties and vulnerability
- Generation of summary statistics for reporting
- Support for filtering and grouping data by various dimensions

This analysis tool helps researchers move beyond individual result examination to understand
the bigger picture of language model vulnerabilities across different experimental conditions.
It transforms raw merged data into actionable insights about model safety and jailbreak
effectiveness.

Usage:
    python analyze_merged_data.py [options]

The script outputs analysis results that can be used for reporting, visualization, or
further statistical processing.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyze_merged_data():
    """
    Analyze the master CSV file and provide basic statistics.
    """
    # Read the master data file
    print("Reading master data file...")
    df = pd.read_csv('master_data.csv')
    
    print(f"Total number of experiments: {len(df)}")
    
    # Count by source file
    print("\nExperiments by source file:")
    source_counts = df['source_file'].value_counts()
    for source, count in source_counts.items():
        print(f"  {source}: {count} experiments")
    
    # Count by jailbreak tactic
    print("\nExperiments by jailbreak tactic:")
    tactic_counts = df['jailbreak_tactic'].value_counts()
    for tactic, count in tactic_counts.items():
        print(f"  {tactic}: {count} experiments")
    
    # Count by turn type
    print("\nExperiments by turn type:")
    turn_counts = df['turn_type'].value_counts()
    for turn_type, count in turn_counts.items():
        print(f"  {turn_type}: {count} experiments")
    
    # Count by target model
    print("\nTop 10 target models by experiment count:")
    model_counts = df['target_model'].value_counts().head(10)
    for model, count in model_counts.items():
        print(f"  {model}: {count} experiments")
    
    # Goal achieved stats
    print("\nSuccess rate by jailbreak tactic:")
    for tactic in df['jailbreak_tactic'].unique():
        tactic_df = df[df['jailbreak_tactic'] == tactic]
        success_rate = tactic_df['goal_achieved'].mean() * 100
        print(f"  {tactic}: {success_rate:.2f}%")
    
    # Success rate by turn type
    print("\nSuccess rate by turn type:")
    for turn_type in df['turn_type'].unique():
        turn_df = df[df['turn_type'] == turn_type]
        success_rate = turn_df['goal_achieved'].mean() * 100
        print(f"  {turn_type}: {success_rate:.2f}%")
    
    # Success rate by source file
    print("\nSuccess rate by source file:")
    for source in df['source_file'].unique():
        source_df = df[df['source_file'] == source]
        success_rate = source_df['goal_achieved'].mean() * 100
        print(f"  {source}: {success_rate:.2f}%")
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    analyze_merged_data() 