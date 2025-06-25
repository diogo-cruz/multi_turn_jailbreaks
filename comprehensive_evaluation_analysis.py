#!/usr/bin/env python3
"""
Comprehensive Three-Way Evaluation System Analysis

This script provides a thorough comparison of three evaluation systems:
1. Original goal_achieved evaluations (baseline)
2. Human expert evaluations  
3. AI meta-evaluations

Designed for publication-quality analysis and reporting.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import scipy.stats as stats
from sklearn.metrics import cohen_kappa_score, confusion_matrix, classification_report
import warnings
warnings.filterwarnings('ignore')

class EvaluationSystemAnalysis:
    """Comprehensive analysis of three evaluation systems"""
    
    def __init__(self):
        self.data = {}
        self.metrics = {}
        self.load_data()
        
    def load_data(self):
        """Load data from all three evaluation systems"""
        
        # Load comprehensive human vs AI data (contains human evaluations and AI meta-evaluations)
        try:
            human_ai_df = pd.read_csv('comprehensive_scores_sample.csv')
            print(f"Loaded {len(human_ai_df)} cases from human vs AI comparison")
            self.data['human_ai'] = human_ai_df
        except FileNotFoundError:
            print("Warning: comprehensive_scores_sample.csv not found")
            self.data['human_ai'] = pd.DataFrame()
        
        # Load original vs AI data (contains original evaluations and AI meta-evaluations)
        try:
            original_ai_df = pd.read_csv('original_ai_comparison.csv')
            print(f"Loaded {len(original_ai_df)} cases from original vs AI comparison")
            self.data['original_ai'] = original_ai_df
        except FileNotFoundError:
            print("Warning: original_ai_comparison.csv not found")
            self.data['original_ai'] = pd.DataFrame()
            
        # Create three-way comparison dataset by merging on filename
        self.create_three_way_dataset()
        
    def create_three_way_dataset(self):
        """Create a unified dataset with all three evaluation systems"""
        
        if self.data['human_ai'].empty or self.data['original_ai'].empty:
            print("Cannot create three-way dataset: missing input data")
            self.data['three_way'] = pd.DataFrame()
            return
        
        # Prepare human vs AI data
        human_ai = self.data['human_ai'].copy()
        human_ai['filename_clean'] = human_ai['filename'].apply(lambda x: x.replace('.jsonl', ''))
        
        # Prepare original vs AI data  
        original_ai = self.data['original_ai'].copy()
        original_ai['filename_clean'] = original_ai['file_name'].apply(lambda x: x.replace('.jsonl', ''))
        
        # Merge datasets
        three_way = pd.merge(
            human_ai[['filename_clean', 'filename', 'test_case', 'tactic', 'human_decision', 
                     'ai_goal_achieved', 'ai_found_issues']],
            original_ai[['filename_clean', 'original_goal_achieved', 'target_model']],
            on='filename_clean',
            how='inner'
        )
        
        # Clean up column names and create standardized evaluations
        three_way['human_jailbroken'] = three_way['human_decision'] == 'true_positive'
        three_way['ai_meta_jailbroken'] = ~three_way['ai_found_issues']  # AI says jailbroken if no issues found
        
        print(f"Created three-way dataset with {len(three_way)} overlapping cases")
        self.data['three_way'] = three_way
        
    def calculate_agreement_metrics(self):
        """Calculate comprehensive agreement metrics between all evaluation pairs"""
        
        if self.data['three_way'].empty:
            return {}
        
        df = self.data['three_way']
        metrics = {}
        
        # Binary evaluations for agreement calculation
        original = df['original_goal_achieved'].astype(bool)
        human = df['human_jailbroken'].astype(bool)  
        ai_meta = df['ai_meta_jailbroken'].astype(bool)
        
        # Pairwise agreement rates
        metrics['original_human_agreement'] = (original == human).mean()
        metrics['original_ai_agreement'] = (original == ai_meta).mean()
        metrics['human_ai_agreement'] = (human == ai_meta).mean()
        
        # Cohen's Kappa (inter-rater reliability)
        try:
            metrics['original_human_kappa'] = cohen_kappa_score(original, human)
            metrics['original_ai_kappa'] = cohen_kappa_score(original, ai_meta)
            metrics['human_ai_kappa'] = cohen_kappa_score(human, ai_meta)
        except:
            metrics['original_human_kappa'] = np.nan
            metrics['original_ai_kappa'] = np.nan
            metrics['human_ai_kappa'] = np.nan
        
        # Evaluation system statistics
        metrics['original_positive_rate'] = original.mean()
        metrics['human_positive_rate'] = human.mean()
        metrics['ai_meta_positive_rate'] = ai_meta.mean()
        
        # Three-way agreement
        three_way_agreement = (original == human) & (human == ai_meta)
        metrics['three_way_agreement_rate'] = three_way_agreement.mean()
        metrics['three_way_agreement_count'] = three_way_agreement.sum()
        
        self.metrics['agreement'] = metrics
        return metrics
        
    def analyze_disagreement_patterns(self):
        """Analyze patterns in disagreements between evaluation systems"""
        
        if self.data['three_way'].empty:
            return {}
        
        df = self.data['three_way']
        patterns = {}
        
        # Create disagreement categories
        original = df['original_goal_achieved'].astype(bool)
        human = df['human_jailbroken'].astype(bool)
        ai_meta = df['ai_meta_jailbroken'].astype(bool)
        
        # Disagreement pattern categories
        disagreement_patterns = []
        for i, row in df.iterrows():
            o, h, a = original.iloc[i], human.iloc[i], ai_meta.iloc[i]
            if o and h and a:
                disagreement_patterns.append('All_Agree_Jailbroken')
            elif not o and not h and not a:
                disagreement_patterns.append('All_Agree_Not_Jailbroken')
            elif o and h and not a:
                disagreement_patterns.append('Original_Human_vs_AI')
            elif o and not h and a:
                disagreement_patterns.append('Original_AI_vs_Human')
            elif not o and h and a:
                disagreement_patterns.append('Human_AI_vs_Original')
            elif o and not h and not a:
                disagreement_patterns.append('Original_vs_Human_AI')
            elif not o and h and not a:
                disagreement_patterns.append('Human_vs_Original_AI')
            elif not o and not h and a:
                disagreement_patterns.append('AI_vs_Original_Human')
        
        df['disagreement_pattern'] = disagreement_patterns
        patterns['pattern_counts'] = Counter(disagreement_patterns)
        patterns['pattern_percentages'] = {k: v/len(df)*100 for k, v in patterns['pattern_counts'].items()}
        
        # Analyze by test case and tactic
        if 'test_case' in df.columns:
            patterns['by_test_case'] = df.groupby('test_case')['disagreement_pattern'].apply(
                lambda x: Counter(x).most_common()
            ).to_dict()
            
        if 'tactic' in df.columns:
            patterns['by_tactic'] = df.groupby('tactic')['disagreement_pattern'].apply(
                lambda x: Counter(x).most_common()
            ).to_dict()
        
        self.metrics['disagreement_patterns'] = patterns
        return patterns
        
    def analyze_by_characteristics(self):
        """Analyze agreement patterns by different characteristics"""
        
        if self.data['three_way'].empty:
            return {}
        
        df = self.data['three_way']
        characteristics = {}
        
        # By jailbreak tactic
        if 'tactic' in df.columns:
            tactic_analysis = df.groupby('tactic').agg({
                'original_goal_achieved': ['count', 'mean'],
                'human_jailbroken': 'mean',
                'ai_meta_jailbroken': 'mean'
            }).round(3)
            
            # Calculate pairwise agreements by tactic
            tactic_agreements = {}
            for tactic in df['tactic'].unique():
                tactic_df = df[df['tactic'] == tactic]
                if len(tactic_df) > 1:
                    orig = tactic_df['original_goal_achieved'].astype(bool)
                    human = tactic_df['human_jailbroken'].astype(bool)
                    ai = tactic_df['ai_meta_jailbroken'].astype(bool)
                    
                    tactic_agreements[tactic] = {
                        'original_human': (orig == human).mean(),
                        'original_ai': (orig == ai).mean(), 
                        'human_ai': (human == ai).mean(),
                        'count': len(tactic_df)
                    }
            
            characteristics['by_tactic'] = {
                'evaluation_rates': tactic_analysis,
                'agreement_rates': tactic_agreements
            }
        
        # By test case
        if 'test_case' in df.columns:
            test_case_agreements = {}
            for test_case in df['test_case'].unique():
                tc_df = df[df['test_case'] == test_case]
                if len(tc_df) > 1:
                    orig = tc_df['original_goal_achieved'].astype(bool)
                    human = tc_df['human_jailbroken'].astype(bool)
                    ai = tc_df['ai_meta_jailbroken'].astype(bool)
                    
                    test_case_agreements[test_case] = {
                        'original_human': (orig == human).mean(),
                        'original_ai': (orig == ai).mean(),
                        'human_ai': (human == ai).mean(),
                        'count': len(tc_df)
                    }
            
            characteristics['by_test_case'] = test_case_agreements
            
        # By target model (if available)
        if 'target_model' in df.columns:
            model_agreements = {}
            for model in df['target_model'].unique():
                model_df = df[df['target_model'] == model]
                if len(model_df) >= 3:  # Only analyze models with sufficient data
                    orig = model_df['original_goal_achieved'].astype(bool)
                    human = model_df['human_jailbroken'].astype(bool)
                    ai = model_df['ai_meta_jailbroken'].astype(bool)
                    
                    model_agreements[model] = {
                        'original_human': (orig == human).mean(),
                        'original_ai': (orig == ai).mean(),
                        'human_ai': (human == ai).mean(),
                        'count': len(model_df)
                    }
            
            characteristics['by_model'] = model_agreements
        
        self.metrics['characteristics'] = characteristics
        return characteristics
    
    def statistical_significance_tests(self):
        """Perform statistical tests on evaluation system differences"""
        
        if self.data['three_way'].empty:
            return {}
        
        df = self.data['three_way']
        tests = {}
        
        original = df['original_goal_achieved'].astype(int)
        human = df['human_jailbroken'].astype(int)
        ai_meta = df['ai_meta_jailbroken'].astype(int)
        
        # McNemar's test for paired binary classifications
        def mcnemar_test(system1, system2):
            """McNemar's test for comparing two classifiers"""
            # Create contingency table
            agree_pos = ((system1 == 1) & (system2 == 1)).sum()
            agree_neg = ((system1 == 0) & (system2 == 0)).sum()
            disagree_1pos_2neg = ((system1 == 1) & (system2 == 0)).sum()
            disagree_1neg_2pos = ((system1 == 0) & (system2 == 1)).sum()
            
            # McNemar's test statistic
            if disagree_1pos_2neg + disagree_1neg_2pos > 0:
                mcnemar_stat = (abs(disagree_1pos_2neg - disagree_1neg_2pos) - 1)**2 / (disagree_1pos_2neg + disagree_1neg_2pos)
                p_value = 1 - stats.chi2.cdf(mcnemar_stat, 1)
            else:
                mcnemar_stat = 0
                p_value = 1.0
                
            return {
                'statistic': mcnemar_stat,
                'p_value': p_value,
                'contingency': [[agree_neg, disagree_1neg_2pos], [disagree_1pos_2neg, agree_pos]]
            }
        
        tests['original_vs_human'] = mcnemar_test(original, human)
        tests['original_vs_ai'] = mcnemar_test(original, ai_meta)
        tests['human_vs_ai'] = mcnemar_test(human, ai_meta)
        
        # Chi-square test for independence 
        try:
            contingency_oh = pd.crosstab(original, human)
            chi2_oh, p_oh, dof_oh, expected_oh = stats.chi2_contingency(contingency_oh)
            tests['chi2_original_human'] = {'chi2': chi2_oh, 'p_value': p_oh, 'dof': dof_oh}
            
            contingency_oa = pd.crosstab(original, ai_meta)
            chi2_oa, p_oa, dof_oa, expected_oa = stats.chi2_contingency(contingency_oa)
            tests['chi2_original_ai'] = {'chi2': chi2_oa, 'p_value': p_oa, 'dof': dof_oa}
            
            contingency_ha = pd.crosstab(human, ai_meta)
            chi2_ha, p_ha, dof_ha, expected_ha = stats.chi2_contingency(contingency_ha)
            tests['chi2_human_ai'] = {'chi2': chi2_ha, 'p_value': p_ha, 'dof': dof_ha}
        except:
            tests['chi2_original_human'] = {'chi2': np.nan, 'p_value': np.nan, 'dof': np.nan}
            tests['chi2_original_ai'] = {'chi2': np.nan, 'p_value': np.nan, 'dof': np.nan}
            tests['chi2_human_ai'] = {'chi2': np.nan, 'p_value': np.nan, 'dof': np.nan}
        
        self.metrics['statistical_tests'] = tests
        return tests
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        
        print("="*80)
        print("COMPREHENSIVE THREE-WAY EVALUATION SYSTEM ANALYSIS")
        print("="*80)
        
        # Run all analyses
        agreement_metrics = self.calculate_agreement_metrics()
        disagreement_patterns = self.analyze_disagreement_patterns()
        characteristics = self.analyze_by_characteristics()
        stat_tests = self.statistical_significance_tests()
        
        # Dataset summary
        if not self.data['three_way'].empty:
            df = self.data['three_way']
            print(f"\nDATASET SUMMARY")
            print(f"{'='*50}")
            print(f"Total cases analyzed: {len(df)}")
            print(f"Unique test cases: {df['test_case'].nunique() if 'test_case' in df.columns else 'N/A'}")
            print(f"Unique jailbreak tactics: {df['tactic'].nunique() if 'tactic' in df.columns else 'N/A'}")
            print(f"Unique target models: {df['target_model'].nunique() if 'target_model' in df.columns else 'N/A'}")
        
        # Agreement metrics
        print(f"\nAGREEMENT METRICS")
        print(f"{'='*50}")
        if agreement_metrics:
            print(f"Original vs Human Agreement: {agreement_metrics['original_human_agreement']:.3f}")
            print(f"Original vs AI Meta Agreement: {agreement_metrics['original_ai_agreement']:.3f}")
            print(f"Human vs AI Meta Agreement: {agreement_metrics['human_ai_agreement']:.3f}")
            print(f"\nCohen's Kappa (Inter-rater Reliability):")
            print(f"Original vs Human: {agreement_metrics['original_human_kappa']:.3f}")
            print(f"Original vs AI Meta: {agreement_metrics['original_ai_kappa']:.3f}")
            print(f"Human vs AI Meta: {agreement_metrics['human_ai_kappa']:.3f}")
            print(f"\nEvaluation System Positive Rates:")
            print(f"Original System: {agreement_metrics['original_positive_rate']:.3f}")
            print(f"Human Evaluators: {agreement_metrics['human_positive_rate']:.3f}")
            print(f"AI Meta-Evaluator: {agreement_metrics['ai_meta_positive_rate']:.3f}")
            print(f"\nThree-way Agreement: {agreement_metrics['three_way_agreement_rate']:.3f} ({agreement_metrics['three_way_agreement_count']}/{len(df)} cases)")
        
        # Disagreement patterns
        print(f"\nDISAGREEMENT PATTERNS")
        print(f"{'='*50}")
        if disagreement_patterns and 'pattern_percentages' in disagreement_patterns:
            for pattern, percentage in disagreement_patterns['pattern_percentages'].items():
                count = disagreement_patterns['pattern_counts'][pattern]
                print(f"{pattern}: {percentage:.1f}% ({count} cases)")
        
        # Statistical significance tests
        print(f"\nSTATISTICAL SIGNIFICANCE TESTS")
        print(f"{'='*50}")
        if stat_tests:
            print("McNemar's Test (p-values for comparing paired classifications):")
            print(f"Original vs Human: p = {stat_tests['original_vs_human']['p_value']:.4f}")
            print(f"Original vs AI Meta: p = {stat_tests['original_vs_ai']['p_value']:.4f}")
            print(f"Human vs AI Meta: p = {stat_tests['human_vs_ai']['p_value']:.4f}")
            
            print("\nChi-square Test for Independence (p-values):")
            print(f"Original vs Human: p = {stat_tests['chi2_original_human']['p_value']:.4f}")
            print(f"Original vs AI Meta: p = {stat_tests['chi2_original_ai']['p_value']:.4f}")
            print(f"Human vs AI Meta: p = {stat_tests['chi2_human_ai']['p_value']:.4f}")
        
        # Analysis by characteristics
        print(f"\nANALYSIS BY JAILBREAK TACTIC")
        print(f"{'='*50}")
        if characteristics and 'by_tactic' in characteristics:
            for tactic, metrics in characteristics['by_tactic']['agreement_rates'].items():
                print(f"\n{tactic.upper()} (n={metrics['count']}):")
                print(f"  Original vs Human: {metrics['original_human']:.3f}")
                print(f"  Original vs AI Meta: {metrics['original_ai']:.3f}")
                print(f"  Human vs AI Meta: {metrics['human_ai']:.3f}")
        
        return {
            'agreement_metrics': agreement_metrics,
            'disagreement_patterns': disagreement_patterns, 
            'characteristics': characteristics,
            'statistical_tests': stat_tests
        }

def main():
    """Main analysis function"""
    
    print("Initializing comprehensive evaluation system analysis...")
    analyzer = EvaluationSystemAnalysis()
    
    if analyzer.data['three_way'].empty:
        print("Error: Could not create three-way dataset. Check that required CSV files exist.")
        return
    
    # Generate comprehensive report
    results = analyzer.generate_comprehensive_report()
    
    # Save results to JSON for further analysis
    import json
    with open('comprehensive_evaluation_analysis_results.json', 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        json_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                filtered_dict = {}
                for k, v in value.items():
                    try:
                        if not pd.isna(v) and isinstance(v, (int, float, str, bool)):
                            filtered_dict[k] = convert_numpy(v)
                        elif isinstance(v, (dict, list)):
                            filtered_dict[k] = v
                    except (TypeError, ValueError):
                        filtered_dict[k] = str(v)
                json_results[key] = filtered_dict
            else:
                json_results[key] = convert_numpy(value)
        
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\nAnalysis complete! Results saved to 'comprehensive_evaluation_analysis_results.json'")
    print(f"Three-way dataset with {len(analyzer.data['three_way'])} cases ready for visualization.")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()