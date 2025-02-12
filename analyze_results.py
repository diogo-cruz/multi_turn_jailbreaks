import os
import re
import json
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple

def extract_score(text: str, pattern: str) -> Optional[float]:
    """Extract numerical score from text using regex pattern"""
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None

def extract_round_scores(jsonl_path: Path) -> Tuple[List[int], bool, int]:
    """Extract scores for each round and goal achievement status from JSONL file"""
    try:
        scores = []
        goal_achieved = False
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
            
            # Process each line
            for line in lines:
                data = json.loads(line)
                if 'round' in data and 'score' in data:
                    try:
                        score = int(data['score']) if data['score'].isdigit() else None
                        scores.append(score)
                    except (ValueError, AttributeError):
                        scores.append(None)
                elif 'goal_achieved' in data:
                    goal_achieved = data['goal_achieved']
        
        return scores, goal_achieved, len([s for s in scores if s is not None])
    except Exception as e:
        print(f"Error reading round scores from {jsonl_path}: {str(e)}")
        return [], False, 0

def extract_jsonl_metadata(jsonl_path: Path) -> Dict:
    """Extract metadata from the first line of a JSONL file"""
    try:
        with open(jsonl_path, 'r') as f:
            first_line = f.readline().strip()
            metadata = json.loads(first_line)
            
            # Extract round scores and goal achievement
            scores, goal_achieved, valid_rounds = extract_round_scores(jsonl_path)
            
            # Calculate score statistics
            non_none_scores = [s for s in scores if s is not None]
            avg_score = np.mean(non_none_scores) if non_none_scores else None
            max_score = max(non_none_scores) if non_none_scores else None
            
            # Extract relevant fields
            return {
                'target_model': metadata.get('target_model'),
                'attacker_model': metadata.get('attacker_model'),
                'test_case': metadata.get('test_case'),
                'jailbreak_tactic': metadata.get('jailbreak_tactic'),
                'max_rounds': metadata.get('max_rounds'),
                'turn_type': metadata.get('turn_type'),
                'target_system': metadata.get('target_system'),
                'task': metadata.get('task'),
                'goal_achieved': bool(goal_achieved),
                'completed_rounds': valid_rounds,
                'average_round_score': avg_score,
                'max_round_score': max_score,
                'round_scores': scores
            }
    except Exception as e:
        print(f"Error reading JSONL metadata from {jsonl_path}: {str(e)}")
        return {}

def standardize_test_case_type(test_type: str) -> str:
    """Standardize test case type formatting"""
    if not test_type:
        return "unknown"
    return test_type.lower().strip()

def extract_primary_issues(content: str) -> List[str]:
    """Extract primary issues from the analysis content"""
    issues_section = re.search(r'Primary Issues Identified:(.+?)(?=Secondary Issues:|###|$)', content, re.DOTALL)
    if not issues_section:
        return []
    
    issues_text = issues_section.group(1)
    issues = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', issues_text, re.DOTALL)
    return [issue.strip() for issue in issues if issue.strip()]

def categorize_issues(issues: List[str]) -> Dict[str, bool]:
    """Categorize issues based on predefined problem categories and sub-categories"""
    categories = {
        # Scoring Metric Issues
        'scoring_metric_issues': False,
        'scoring_rubric_inconsistency': False,  # Dynamic rubric generation issues
        'scoring_false_positives': False,       # False positive detection problems
        'scoring_length_bias': False,           # Length-based scoring bias
        
        # Model Response Issues
        'model_response_issues': False,
        'response_hallucination': False,        # Heavy hallucination
        'response_nonsensical': False,          # Nonsensical outputs
        'response_incoherent': False,           # Incoherent responses
        
        # Attacker Model Issues
        'attacker_model_issues': False,
        'attacker_refusal': False,              # GPT-4 refusing to generate prompts
        'attacker_inefficient': False,          # Inefficient attack strategies
        'attacker_random': False,               # Random/unfocused attempts
        
        # Test Case Definition Issues
        'test_case_definition_issues': False,
        'definition_vague': False,              # Vague success criteria
        'definition_ambiguous': False,          # Ambiguous objectives
        'definition_unclear': False,            # Unclear system prompts
        
        # Technical Implementation Issues
        'technical_implementation_issues': False,
        'implementation_refusal': False,        # Handling model refusals
        'implementation_conversation': False,    # Conversation tracking issues
        'implementation_rounds': False          # Round management problems
    }
    
    keywords = {
        # Scoring Metric Issues
        'scoring_rubric_inconsistency': [
            'rubric', 'scoring criteria', 'evaluation criteria', 'inconsistent', 
            'scoring system', 'scoring shows', 'criteria appears', 'variation in strictness'
        ],
        'scoring_false_positives': [
            'false positive', 'misclassified', 'misidentified', 'wrong classification',
            'vulnerability to false', 'potentially misclassified'
        ],
        'scoring_length_bias': [
            'length bias', 'response length', 'lengthy response', 'long output',
            'focus on content rather than length'
        ],
        
        # Model Response Issues
        'response_hallucination': [
            'hallucination', 'fabricated', 'made up', 'invented', 'speculative',
            'unverified information'
        ],
        'response_nonsensical': [
            'nonsensical', 'gibberish', 'meaningless', 'illogical', 'incoherent output'
        ],
        'response_incoherent': [
            'incoherent', 'inconsistent response', 'unclear response', 'confused',
            'poorly structured'
        ],
        
        # Attacker Model Issues
        'attacker_refusal': [
            'refuses to generate', 'attacker refusal', 'gpt-4 refuses', 'won\'t generate',
            'limited success', 'ineffective against'
        ],
        'attacker_inefficient': [
            'inefficient attack', 'ineffective strategy', 'poor attack', 'limited sophistication',
            'straightforward attempts', 'basic approach'
        ],
        'attacker_random': [
            'random attempts', 'unfocused', 'scattered approach', 'lacks sophistication',
            'without sophisticated'
        ],
        
        # Test Case Definition Issues
        'definition_vague': [
            'vague criteria', 'unclear criteria', 'undefined success', 'unclear standards',
            'needs clearer definition'
        ],
        'definition_ambiguous': [
            'ambiguous', 'unclear objective', 'unclear goal', 'multiple interpretations'
        ],
        'definition_unclear': [
            'unclear prompt', 'unclear system', 'unclear instruction', 'needs better specification'
        ],
        
        # Technical Implementation Issues
        'implementation_refusal': [
            'handling refusal', 'model refusal', 'rejection handling', 'error handling',
            'handling of model refusals'
        ],
        'implementation_conversation': [
            'conversation tracking', 'dialogue management', 'turn tracking',
            'tracking of interactions'
        ],
        'implementation_rounds': [
            'round management', 'turn counting', 'conversation rounds',
            'tracking rounds'
        ]
    }
    
    # Process each issue
    for issue in issues:
        issue_lower = issue.lower()
        
        # Check each keyword set
        for category, terms in keywords.items():
            if any(term.lower() in issue_lower for term in terms):
                categories[category] = True
                
                # Set parent category
                if category.startswith('scoring_'):
                    categories['scoring_metric_issues'] = True
                elif category.startswith('response_'):
                    categories['model_response_issues'] = True
                elif category.startswith('attacker_'):
                    categories['attacker_model_issues'] = True
                elif category.startswith('definition_'):
                    categories['test_case_definition_issues'] = True
                elif category.startswith('implementation_'):
                    categories['technical_implementation_issues'] = True
    
    return categories

def parse_analysis_file(file_path: Path) -> Optional[Dict]:
    """Parse a single analysis markdown file and extract metrics"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract basic information
        file_name = re.search(r'File Name: (.+?)\.jsonl', content)
        file_name = file_name.group(1) if file_name else None
        
        # Get corresponding JSONL metadata
        jsonl_path = file_path.parent / f"{file_name}.jsonl"
        metadata = extract_jsonl_metadata(jsonl_path) if jsonl_path.exists() else {}
        
        # Convert any numpy arrays in metadata to lists
        for key, value in metadata.items():
            if isinstance(value, np.ndarray):
                metadata[key] = value.tolist()
            elif isinstance(value, np.generic):
                metadata[key] = value.item()
        
        test_case_type = re.search(r'Test Case Type: (.+?)\n', content)
        test_case_type = test_case_type.group(1) if test_case_type else None
        test_case_type = standardize_test_case_type(test_case_type)
        
        target_behavior = re.search(r'Target Behavior: (.+?)\n', content)
        target_behavior = target_behavior.group(1) if target_behavior else None
        
        # Extract scores using patterns
        metrics = {
            # Scoring Metric Quality
            'rubric_consistency': extract_score(content, r'Rubric Consistency: (\d+)/5'),
            'false_positive_detection': extract_score(content, r'False Positive Detection: (\d+)/5'),
            'response_length_bias': extract_score(content, r'Response Length Bias: (\d+)/5'),
            
            # Response Quality Assessment
            'coherence': extract_score(content, r'Coherence: (\d+)/5'),
            'hallucination_level': extract_score(content, r'Hallucination Level: (\d+)/5'),
            'task_relevance': extract_score(content, r'Task Relevance: (\d+)/5'),
            
            # Attack Strategy Evaluation
            'attack_effectiveness': extract_score(content, r'Attack Effectiveness: (\d+)/5'),
            'strategy_progression': extract_score(content, r'Strategy Progression: (\d+)/5'),
            'prompt_creativity': extract_score(content, r'Prompt Creativity: (\d+)/5'),
            
            # Technical Implementation
            'conversation_tracking': extract_score(content, r'Conversation Tracking: (\d+)/5'),
            'error_handling': extract_score(content, r'Error Handling: (\d+)/5'),
            'response_processing': extract_score(content, r'Response Processing: (\d+)/5'),
            
            # Overall Reliability Score
            'reliability_score': extract_score(content, r'Reliability Score: (\d+)/100'),
        }
        
        # Extract and categorize issues
        primary_issues = extract_primary_issues(content)
        issue_categories = categorize_issues(primary_issues)
        metrics.update(issue_categories)
        
        # Calculate aggregate scores
        score_groups = {
            'scoring_quality': ['rubric_consistency', 'false_positive_detection', 'response_length_bias'],
            'response_quality': ['coherence', 'hallucination_level', 'task_relevance'],
            'attack_quality': ['attack_effectiveness', 'strategy_progression', 'prompt_creativity'],
            'technical_quality': ['conversation_tracking', 'error_handling', 'response_processing']
        }
        
        for group_name, metrics_list in score_groups.items():
            scores = [metrics[m] for m in metrics_list if metrics[m] is not None]
            metrics[group_name] = float(np.mean(scores)) if scores else None
        
        # Add basic information and metadata to metrics
        metrics.update({
            'file_name': file_name,
            'test_case_type': test_case_type,
            'target_behavior': target_behavior,
            **metadata  # Add all metadata fields
        })
        
        return metrics
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

def generate_analysis_plots(df: pd.DataFrame, output_dir: str):
    """Generate visualization plots for the analysis"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Set style for better-looking plots
    plt.style.use('seaborn')
    
    # Convert round_scores back to list if it was converted to string
    if 'round_scores' in df.columns:
        df['round_scores'] = df['round_scores'].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else x)
    
    # Extract model size from target_model name
    def extract_model_size(model_name):
        if pd.isna(model_name):
            return None
        size_match = re.search(r'(\d+)b', str(model_name).lower())
        if size_match:
            return float(size_match.group(1))
        return None
    
    df['model_size'] = df['target_model'].apply(extract_model_size)
    
    # Calculate max rounds safely
    valid_scores = [scores for scores in df['round_scores'] if isinstance(scores, list) and scores]
    max_rounds = max(len(scores) for scores in valid_scores) if valid_scores else 0
    
    # 1. Score distributions
    plt.figure(figsize=(12, 6))
    score_cols = ['scoring_quality', 'response_quality', 'attack_quality', 'technical_quality']
    score_data = df[score_cols].dropna()
    if not score_data.empty:
        score_data.boxplot()
        plt.title('Distribution of Quality Scores')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/score_distributions.png')
    plt.close()
    
    # 2. Correlation heatmap
    plt.figure(figsize=(12, 10))
    numeric_cols = ['reliability_score', 'scoring_quality', 'response_quality', 
                   'attack_quality', 'technical_quality', 'average_round_score']
    corr_data = df[numeric_cols].dropna()
    if not corr_data.empty:
        sns.heatmap(corr_data.corr(), annot=True, cmap='coolwarm', center=0)
        plt.title('Correlation Matrix of Key Metrics')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/correlation_heatmap.png')
    plt.close()
    
    # 3. Round scores progression
    if max_rounds > 0:
        plt.figure(figsize=(12, 6))
        round_data = []
        round_sizes = []
        
        for round_idx in range(max_rounds):
            scores = [scores[round_idx] for scores in df['round_scores'] 
                     if isinstance(scores, list) and round_idx < len(scores) and scores[round_idx] is not None]
            if scores:
                round_data.append(scores)
                round_sizes.append(len(scores))
        
        if round_data:
            bp = plt.boxplot(round_data)
            plt.title('Score Progression by Round')
            plt.xlabel('Round Number')
            plt.ylabel('Score')
            
            # Add sample size annotations
            for i, size in enumerate(round_sizes, 1):
                plt.text(i, plt.ylim()[0], f'n={size}', horizontalalignment='center', verticalalignment='top')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/round_progression.png')
        plt.close()
    
    # 4. Attack effectiveness vs. model size by test case
    plt.figure(figsize=(12, 6))
    df_with_size = df[df['model_size'].notna() & df['attack_effectiveness'].notna()]
    if not df_with_size.empty:
        for test_case in df_with_size['test_case'].unique():
            test_data = df_with_size[df_with_size['test_case'] == test_case]
            if not test_data.empty:
                plt.scatter(test_data['model_size'], test_data['attack_effectiveness'],
                           label=test_case, alpha=0.6)
        
        plt.xlabel('Model Size (B parameters)')
        plt.ylabel('Attack Effectiveness Score')
        plt.title('Attack Effectiveness vs. Model Size by Test Case')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/attack_effectiveness_by_size.png')
    plt.close()
    
    # 5. Distribution of rounds to success
    plt.figure(figsize=(10, 6))
    successful_attempts = df[df['goal_achieved'] == True].copy()
    if len(successful_attempts) > 0 and 'completed_rounds' in successful_attempts.columns:
        sns.histplot(data=successful_attempts, x='completed_rounds', bins=20)
        plt.title('Distribution of Rounds to Success')
        plt.xlabel('Number of Rounds')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/rounds_to_success.png')
    plt.close()
    
    # 6. Issue frequency by test case
    issue_cols = ['scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
                 'test_case_definition_issues', 'technical_implementation_issues']
    
    plt.figure(figsize=(14, 7))
    issue_by_test = df.groupby('test_case')[issue_cols].mean()
    issue_by_test.plot(kind='bar', stacked=True)
    plt.title('Issue Frequency by Test Case')
    plt.xlabel('Test Case')
    plt.ylabel('Proportion of Issues')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/issue_by_test_case.png')
    plt.close()
    
    # Add new plot for detailed issue breakdown
    plt.figure(figsize=(15, 10))
    
    # Get all issue columns
    issue_cols = [col for col in df.columns if any(x in col for x in [
        'scoring_', 'response_', 'attacker_', 'definition_', 'implementation_'
    ])]
    
    # Separate main issues and sub-issues
    main_issues = [col for col in issue_cols if col.endswith('_issues')]
    sub_issues = [col for col in issue_cols if not col.endswith('_issues')]
    
    # Create subplot for main issues
    plt.subplot(2, 1, 1)
    main_issue_data = df[main_issues].mean() * 100
    main_issue_data.plot(kind='bar')
    plt.title('Main Issue Categories')
    plt.ylabel('Percentage of Cases')
    plt.xticks(rotation=45, ha='right')
    
    # Create subplot for sub-issues
    plt.subplot(2, 1, 2)
    sub_issue_data = df[sub_issues].mean() * 100
    sub_issue_data.plot(kind='bar')
    plt.title('Detailed Issue Breakdown')
    plt.ylabel('Percentage of Cases')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/detailed_issue_breakdown.png')
    plt.close()
    
    # Add heatmap showing correlation between issues
    plt.figure(figsize=(15, 12))
    issue_corr = df[issue_cols].corr()
    sns.heatmap(issue_corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
    plt.title('Issue Correlation Matrix')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/issue_correlations.png')
    plt.close()
    
    # 7. Performance by model size
    plt.figure(figsize=(12, 6))
    model_perf = df.groupby('model_size').agg({
        'reliability_score': ['mean', 'std', 'count'],
        'goal_achieved': 'mean'
    }).round(2)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # Plot reliability score
    ax1.errorbar(model_perf.index, model_perf[('reliability_score', 'mean')],
                yerr=model_perf[('reliability_score', 'std')],
                fmt='o-', color='blue', label='Reliability Score')
    ax1.set_xlabel('Model Size (B parameters)')
    ax1.set_ylabel('Reliability Score', color='blue')
    
    # Plot success rate
    ax2.plot(model_perf.index, model_perf[('goal_achieved', 'mean')] * 100,
             'r--', label='Success Rate')
    ax2.set_ylabel('Success Rate (%)', color='red')
    
    plt.title('Model Performance by Size')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/model_size_performance.png')
    plt.close()
    
    # 8. Success rate by jailbreak tactic and test case
    plt.figure(figsize=(14, 7))
    success_by_tactic_test = df.pivot_table(
        values='goal_achieved',
        index='test_case',
        columns='jailbreak_tactic',
        aggfunc='mean'
    ) * 100
    
    sns.heatmap(success_by_tactic_test, annot=True, fmt='.1f', cmap='YlOrRd')
    plt.title('Success Rate (%) by Tactic and Test Case')
    plt.xlabel('Jailbreak Tactic')
    plt.ylabel('Test Case')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/success_by_tactic_test.png')
    plt.close()
    
    # 9. Quality metrics by jailbreak tactic
    plt.figure(figsize=(14, 7))
    tactic_metrics = df.groupby('jailbreak_tactic')[score_cols].mean()
    tactic_metrics.plot(kind='bar', width=0.8)
    plt.title('Quality Metrics by Jailbreak Tactic')
    plt.xlabel('Jailbreak Tactic')
    plt.ylabel('Average Score')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/quality_by_tactic.png')
    plt.close()

def analyze_results(results_dir: str) -> pd.DataFrame:
    """Analyze all markdown files in the results directory"""
    results = []
    
    # Find all analysis markdown files
    analysis_files = Path(results_dir).glob('*_analysis.md')
    
    for file_path in analysis_files:
        metrics = parse_analysis_file(file_path)
        if metrics:
            # Convert any numpy arrays to lists before adding to results
            for key, value in metrics.items():
                if isinstance(value, np.ndarray):
                    metrics[key] = value.tolist()
                elif isinstance(value, np.generic):
                    metrics[key] = value.item()
            results.append(metrics)
    
    # Create DataFrame with explicit dtype specification
    df = pd.DataFrame(results)
    
    # Convert numeric columns to float
    numeric_cols = [
        'reliability_score', 'scoring_quality', 'response_quality', 'attack_quality', 'technical_quality',
        'rubric_consistency', 'false_positive_detection', 'response_length_bias',
        'coherence', 'hallucination_level', 'task_relevance',
        'attack_effectiveness', 'strategy_progression', 'prompt_creativity',
        'conversation_tracking', 'error_handling', 'response_processing',
        'average_round_score', 'max_round_score'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert boolean columns
    bool_cols = [
        'goal_achieved', 'scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
        'test_case_definition_issues', 'technical_implementation_issues'
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    # Convert round_scores to string representation to avoid numpy array issues
    if 'round_scores' in df.columns:
        df['round_scores'] = df['round_scores'].apply(lambda x: str(x) if x is not None else None)
    
    # Reorder columns for better readability
    column_order = [col for col in [
        'file_name', 'test_case_type', 'target_behavior',
        'reliability_score',
        'scoring_quality', 'response_quality', 'attack_quality', 'technical_quality',
        'rubric_consistency', 'false_positive_detection', 'response_length_bias',
        'coherence', 'hallucination_level', 'task_relevance',
        'attack_effectiveness', 'strategy_progression', 'prompt_creativity',
        'conversation_tracking', 'error_handling', 'response_processing',
        'scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
        'test_case_definition_issues', 'technical_implementation_issues',
        'target_model', 'attacker_model', 'test_case', 'jailbreak_tactic', 'max_rounds',
        'turn_type', 'target_system', 'task',
        'goal_achieved', 'completed_rounds', 'average_round_score', 'max_round_score', 'round_scores'
    ] if col in df.columns]
    
    df = df[column_order]
    return df

def generate_summary_report(df: pd.DataFrame) -> str:
    """Generate a detailed summary report of the analysis"""
    report = []
    report.append("# Jailbreak Analysis Summary Report\n")
    
    # Basic statistics
    report.append("## Overview")
    report.append(f"Total analyses: {len(df)}")
    report.append(f"Test case types: {df['test_case_type'].value_counts().to_dict()}")
    report.append(f"Jailbreak tactics: {df['jailbreak_tactic'].value_counts().to_dict()}")
    report.append(f"Target models: {df['target_model'].value_counts().to_dict()}")
    
    # Success rates
    report.append("\n## Success Rates")
    try:
        df['goal_achieved'] = df['goal_achieved'].fillna(False)
        overall_success = df['goal_achieved'].mean() * 100
        report.append(f"Overall success rate: {overall_success:.1f}%")
        
        # Success by tactic
        report.append("\nSuccess rates by tactic:")
        tactic_success = df.groupby('jailbreak_tactic').agg({
            'goal_achieved': ['mean', 'count']
        })
        for tactic in tactic_success.index:
            success_rate = tactic_success.loc[tactic, ('goal_achieved', 'mean')] * 100
            count = tactic_success.loc[tactic, ('goal_achieved', 'count')]
            report.append(f"- {tactic}: {success_rate:.1f}% ({int(count)} attempts)")
        
        # Success by model size
        report.append("\nSuccess rates by model size:")
        df['model_size'] = df['target_model'].str.extract(r'(\d+)b').astype(float)
        size_success = df.groupby('model_size').agg({
            'goal_achieved': ['mean', 'count']
        }).round(2)
        for size in size_success.index:
            success_rate = size_success.loc[size, ('goal_achieved', 'mean')] * 100
            count = size_success.loc[size, ('goal_achieved', 'count')]
            report.append(f"- {int(size)}B parameters: {success_rate:.1f}% ({int(count)} attempts)")
    except Exception as e:
        report.append(f"Error calculating success rates: {str(e)}")
    
    # Round statistics
    report.append("\n## Round Statistics")
    try:
        completed_rounds_mean = df['completed_rounds'].mean()
        report.append(f"Average rounds to completion: {completed_rounds_mean:.1f}")
        
        successful_rounds = df[df['goal_achieved']]['completed_rounds']
        if len(successful_rounds) > 0:
            report.append(f"Average rounds for successful attempts: {successful_rounds.mean():.1f}")
            report.append(f"Max rounds for successful attempts: {successful_rounds.max():.0f}")
    except Exception as e:
        report.append(f"Error calculating round statistics: {str(e)}")
    
    # Aggregate scores
    report.append("\n## Aggregate Scores (0-5 scale)")
    score_types = ['scoring_quality', 'response_quality', 'attack_quality', 'technical_quality']
    for score_type in score_types:
        stats = df[score_type].describe()
        report.append(f"\n### {score_type.replace('_', ' ').title()}")
        report.append(f"- Mean: {stats['mean']:.2f}")
        report.append(f"- Median: {stats['50%']:.2f}")
        report.append(f"- Std Dev: {stats['std']:.2f}")
    
    # Performance by test case
    report.append("\n## Performance by Test Case")
    test_case_stats = df.groupby('test_case').agg({
        'reliability_score': ['mean', 'std', 'count'],
        'goal_achieved': 'mean'
    }).round(2)
    
    for test_case in test_case_stats.index:
        report.append(f"\n### {test_case}")
        report.append(f"- Mean reliability: {test_case_stats.loc[test_case, ('reliability_score', 'mean')]:.2f}")
        report.append(f"- Success rate: {test_case_stats.loc[test_case, ('goal_achieved', 'mean')]*100:.1f}%")
        report.append(f"- Std Dev: {test_case_stats.loc[test_case, ('reliability_score', 'std')]:.2f}")
        report.append(f"- Number of tests: {int(test_case_stats.loc[test_case, ('reliability_score', 'count')])}")
    
    # Issue analysis
    report.append("\n## Issue Analysis")
    issue_cols = ['scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
                 'test_case_definition_issues', 'technical_implementation_issues']
    issue_counts = df[issue_cols].sum()
    for issue, count in issue_counts.items():
        report.append(f"- {issue.replace('_', ' ').title()}: {count} cases ({(count/len(df)*100):.1f}%)")
    
    return "\n".join(report)

if __name__ == "__main__":
    results_dir = "results"
    output_dir = "analysis_output"
    
    # Perform analysis
    df = analyze_results(results_dir)
    
    # Generate visualizations
    generate_analysis_plots(df, output_dir)
    
    # Generate and save summary report
    report = generate_summary_report(df)
    with open(f"{output_dir}/summary_report.md", "w") as f:
        f.write(report)
    
    # Save detailed results
    df.to_csv(f'{output_dir}/jailbreak_analysis_results.csv', index=False)
    
    print(f"Analysis complete. Results saved to {output_dir}/")
    print("\nSummary Report:")
    print(report) 