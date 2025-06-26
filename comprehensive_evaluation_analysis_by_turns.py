#!/usr/bin/env python3
"""
Comprehensive Three-Way Evaluation System Analysis - By Turn Type

This script provides a thorough comparison of three evaluation systems:
1. Original goal_achieved evaluations (baseline)
2. Human expert evaluations  
3. AI meta-evaluations

With separate analysis for single-turn vs multi-turn cases.
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

class EvaluationSystemAnalysisByTurns:
    """Comprehensive analysis of three evaluation systems separated by turn type"""
    
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
        
        # Extract turn type from filename
        three_way['turn_type'] = three_way['filename'].apply(self.extract_turn_type)
        
        print(f"Created three-way dataset with {len(three_way)} overlapping cases")
        
        # Split by turn type
        single_turn = three_way[three_way['turn_type'] == 'single_turn'].copy()
        multi_turn = three_way[three_way['turn_type'] == 'multi_turn'].copy()
        
        print(f"Single-turn cases: {len(single_turn)}")
        print(f"Multi-turn cases: {len(multi_turn)}")
        
        self.data['three_way'] = three_way
        self.data['single_turn'] = single_turn
        self.data['multi_turn'] = multi_turn
        
    def extract_turn_type(self, filename):
        """Extract turn type from filename"""
        if 'single_turn' in filename:
            return 'single_turn'
        elif 'multi_turn' in filename:
            return 'multi_turn'
        else:
            return 'unknown'
    
    def calculate_agreement_metrics(self, df, subset_name=""):
        """Calculate comprehensive agreement metrics between all evaluation pairs"""
        
        if df.empty:
            return {}
        
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
        metrics['total_cases'] = len(df)
        
        return metrics
    
    def analyze_by_characteristics(self, df, subset_name=""):
        """Analyze agreement patterns by different characteristics"""
        
        if df.empty:
            return {}
        
        characteristics = {}
        
        # By jailbreak tactic
        if 'tactic' in df.columns:
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
                        'count': len(tactic_df),
                        'original_positive_rate': orig.mean(),
                        'human_positive_rate': human.mean(),
                        'ai_positive_rate': ai.mean()
                    }
            
            characteristics['by_tactic'] = tactic_agreements
        
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
                        'count': len(tc_df),
                        'original_positive_rate': orig.mean(),
                        'human_positive_rate': human.mean(),
                        'ai_positive_rate': ai.mean()
                    }
            
            characteristics['by_test_case'] = test_case_agreements
        
        return characteristics
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report with turn type separation"""
        
        print("="*80)
        print("COMPREHENSIVE THREE-WAY EVALUATION SYSTEM ANALYSIS BY TURN TYPE")
        print("="*80)
        
        # Overall analysis
        overall_metrics = self.calculate_agreement_metrics(self.data['three_way'], "Overall")
        
        # Single-turn analysis
        single_turn_metrics = self.calculate_agreement_metrics(self.data['single_turn'], "Single-turn")
        single_turn_characteristics = self.analyze_by_characteristics(self.data['single_turn'], "Single-turn")
        
        # Multi-turn analysis
        multi_turn_metrics = self.calculate_agreement_metrics(self.data['multi_turn'], "Multi-turn")
        multi_turn_characteristics = self.analyze_by_characteristics(self.data['multi_turn'], "Multi-turn")
        
        # Dataset summary
        print(f"\nDATASET SUMMARY")
        print(f"{'='*50}")
        print(f"Total cases analyzed: {overall_metrics.get('total_cases', 0)}")
        print(f"Single-turn cases: {single_turn_metrics.get('total_cases', 0)}")
        print(f"Multi-turn cases: {multi_turn_metrics.get('total_cases', 0)}")
        
        if not self.data['three_way'].empty:
            df = self.data['three_way']
            print(f"Unique test cases: {df['test_case'].nunique()}")
            print(f"Unique jailbreak tactics: {df['tactic'].nunique()}")
            print(f"Unique target models: {df['target_model'].nunique()}")
        
        # Agreement metrics comparison
        print(f"\nAGREEMENT METRICS COMPARISON")
        print(f"{'='*60}")
        
        metrics_to_compare = [
            ('Original vs Human Agreement', 'original_human_agreement'),
            ('Original vs AI Meta Agreement', 'original_ai_agreement'),
            ('Human vs AI Meta Agreement', 'human_ai_agreement'),
            ('Three-way Agreement Rate', 'three_way_agreement_rate')
        ]
        
        print(f"{'Metric':<35} {'Overall':<10} {'Single-Turn':<12} {'Multi-Turn':<12}")
        print("-" * 70)
        for metric_name, metric_key in metrics_to_compare:
            overall_val = overall_metrics.get(metric_key, 0)
            single_val = single_turn_metrics.get(metric_key, 0)
            multi_val = multi_turn_metrics.get(metric_key, 0)
            print(f"{metric_name:<35} {overall_val:<10.3f} {single_val:<12.3f} {multi_val:<12.3f}")
        
        # System positive rates comparison
        print(f"\nEVALUATION SYSTEM POSITIVE RATES")
        print(f"{'='*60}")
        
        rate_metrics = [
            ('Original System', 'original_positive_rate'),
            ('Human Evaluators', 'human_positive_rate'),
            ('AI Meta-Evaluator', 'ai_meta_positive_rate')
        ]
        
        print(f"{'System':<20} {'Overall':<10} {'Single-Turn':<12} {'Multi-Turn':<12}")
        print("-" * 55)
        for system_name, rate_key in rate_metrics:
            overall_val = overall_metrics.get(rate_key, 0)
            single_val = single_turn_metrics.get(rate_key, 0)
            multi_val = multi_turn_metrics.get(rate_key, 0)
            print(f"{system_name:<20} {overall_val:<10.3f} {single_val:<12.3f} {multi_val:<12.3f}")
        
        # Tactic analysis for single-turn
        print(f"\nSINGLE-TURN ANALYSIS BY JAILBREAK TACTIC")
        print(f"{'='*60}")
        if single_turn_characteristics and 'by_tactic' in single_turn_characteristics:
            for tactic, metrics in single_turn_characteristics['by_tactic'].items():
                print(f"\n{tactic.upper()} (n={metrics['count']}):")
                print(f"  Original vs Human: {metrics['original_human']:.3f}")
                print(f"  Original vs AI Meta: {metrics['original_ai']:.3f}")
                print(f"  Human vs AI Meta: {metrics['human_ai']:.3f}")
        else:
            print("No single-turn tactic data available")
        
        # Tactic analysis for multi-turn
        print(f"\nMULTI-TURN ANALYSIS BY JAILBREAK TACTIC")
        print(f"{'='*60}")
        if multi_turn_characteristics and 'by_tactic' in multi_turn_characteristics:
            for tactic, metrics in multi_turn_characteristics['by_tactic'].items():
                print(f"\n{tactic.upper()} (n={metrics['count']}):")
                print(f"  Original vs Human: {metrics['original_human']:.3f}")
                print(f"  Original vs AI Meta: {metrics['original_ai']:.3f}")
                print(f"  Human vs AI Meta: {metrics['human_ai']:.3f}")
        else:
            print("No multi-turn tactic data available")
        
        # Key insights
        print(f"\nKEY INSIGHTS")
        print(f"{'='*50}")
        
        if single_turn_metrics and multi_turn_metrics:
            single_human_ai = single_turn_metrics.get('human_ai_agreement', 0)
            multi_human_ai = multi_turn_metrics.get('human_ai_agreement', 0)
            
            if single_human_ai > multi_human_ai:
                print(f"• Single-turn cases show higher Human-AI agreement ({single_human_ai:.3f} vs {multi_human_ai:.3f})")
            else:
                print(f"• Multi-turn cases show higher Human-AI agreement ({multi_human_ai:.3f} vs {single_human_ai:.3f})")
            
            single_orig_ai = single_turn_metrics.get('original_ai_agreement', 0)
            multi_orig_ai = multi_turn_metrics.get('original_ai_agreement', 0)
            
            if single_orig_ai > multi_orig_ai:
                print(f"• Single-turn cases show higher Original-AI agreement ({single_orig_ai:.3f} vs {multi_orig_ai:.3f})")
            else:
                print(f"• Multi-turn cases show higher Original-AI agreement ({multi_orig_ai:.3f} vs {single_orig_ai:.3f})")
        
        return {
            'overall_metrics': overall_metrics,
            'single_turn_metrics': single_turn_metrics,
            'multi_turn_metrics': multi_turn_metrics,
            'single_turn_characteristics': single_turn_characteristics,
            'multi_turn_characteristics': multi_turn_characteristics
        }

def main():
    """Main analysis function"""
    
    print("Initializing comprehensive evaluation system analysis by turn type...")
    analyzer = EvaluationSystemAnalysisByTurns()
    
    if analyzer.data['three_way'].empty:
        print("Error: Could not create three-way dataset. Check that required CSV files exist.")
        return
    
    # Generate comprehensive report
    results = analyzer.generate_comprehensive_report()
    
    # Save results to JSON for further analysis
    import json
    with open('comprehensive_evaluation_analysis_by_turns_results.json', 'w') as f:
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
    
    print(f"\nAnalysis complete! Results saved to 'comprehensive_evaluation_analysis_by_turns_results.json'")
    print(f"Three-way dataset with turn type separation ready for visualization.")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()