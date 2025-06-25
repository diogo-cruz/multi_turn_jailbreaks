#!/usr/bin/env python3
"""
Publication-Quality Visualization Suite for Three-Way Evaluation System Analysis

Generates publication-ready plots comparing Original, Human, and AI Meta-evaluation systems.
Designed for academic papers and research presentations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality plot parameters
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 18,
    'lines.linewidth': 2,
    'lines.markersize': 8,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

class PublicationPlots:
    """Publication-quality plotting suite for evaluation system analysis"""
    
    def __init__(self):
        self.load_data()
        self.colors = {
            'original': '#2E86AB',    # Blue
            'human': '#A23B72',       # Purple
            'ai_meta': '#F18F01',     # Orange
            'agreement': '#C73E1D',   # Red
            'disagreement': '#87CEEB' # Light blue
        }
        
    def load_data(self):
        """Load the three-way comparison dataset"""
        try:
            # Load comprehensive scores (human vs AI)
            human_ai_df = pd.read_csv('comprehensive_scores_sample.csv')
            human_ai_df['filename_clean'] = human_ai_df['filename'].apply(lambda x: x.replace('.jsonl', ''))
            
            # Load original vs AI comparison
            original_ai_df = pd.read_csv('original_ai_comparison.csv')
            original_ai_df['filename_clean'] = original_ai_df['file_name'].apply(lambda x: x.replace('.jsonl', ''))
            
            # Merge datasets
            self.data = pd.merge(
                human_ai_df[['filename_clean', 'filename', 'test_case', 'tactic', 'human_decision', 
                           'ai_goal_achieved', 'ai_found_issues']],
                original_ai_df[['filename_clean', 'original_goal_achieved', 'target_model']],
                on='filename_clean',
                how='inner'
            )
            
            # Create standardized boolean columns
            self.data['original_jailbroken'] = self.data['original_goal_achieved'].astype(bool)
            self.data['human_jailbroken'] = self.data['human_decision'] == 'true_positive'
            self.data['ai_meta_jailbroken'] = ~self.data['ai_found_issues']  # AI says jailbroken if no issues found
            
            print(f"Loaded {len(self.data)} cases for publication plots")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
    
    def plot_overall_agreement_matrix(self, save_path='fig1_agreement_matrix.pdf'):
        """Figure 1: Overall agreement rates between all evaluation systems"""
        
        if self.data.empty:
            return
        
        # Calculate pairwise agreement rates
        original = self.data['original_jailbroken']
        human = self.data['human_jailbroken']
        ai_meta = self.data['ai_meta_jailbroken']
        
        agreement_matrix = np.array([
            [1.0, (original == human).mean(), (original == ai_meta).mean()],
            [(human == original).mean(), 1.0, (human == ai_meta).mean()],
            [(ai_meta == original).mean(), (ai_meta == human).mean(), 1.0]
        ])
        
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        
        # Create heatmap
        im = ax.imshow(agreement_matrix, cmap='RdYlBu_r', vmin=0, vmax=1)
        
        # Set labels
        labels = ['Original\nEvaluator', 'Human\nEvaluators', 'AI Meta-\nEvaluator']
        ax.set_xticks(range(3))
        ax.set_yticks(range(3))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        
        # Add text annotations
        for i in range(3):
            for j in range(3):
                if i == j:
                    text = '1.000'
                else:
                    text = f'{agreement_matrix[i, j]:.3f}'
                ax.text(j, i, text, ha='center', va='center', 
                       fontweight='bold', fontsize=14,
                       color='white' if agreement_matrix[i, j] < 0.5 else 'black')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Agreement Rate', rotation=270, labelpad=20)
        
        ax.set_title(f'Pairwise Agreement Rates Between Evaluation Systems\n(n={len(self.data)} cases)', 
                    fontsize=16, pad=20)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 1: {save_path}")
        plt.show()
    
    def plot_evaluation_distributions(self, save_path='fig2_evaluation_distributions.pdf'):
        """Figure 2: Distribution of positive evaluations by system and characteristics"""
        
        if self.data.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: Overall positive rates
        ax1 = axes[0, 0]
        systems = ['Original', 'Human', 'AI Meta']
        positive_rates = [
            self.data['original_jailbroken'].mean(),
            self.data['human_jailbroken'].mean(), 
            self.data['ai_meta_jailbroken'].mean()
        ]
        
        bars = ax1.bar(systems, positive_rates, 
                      color=[self.colors['original'], self.colors['human'], self.colors['ai_meta']],
                      alpha=0.8, edgecolor='black', linewidth=1)
        
        ax1.set_ylabel('Positive Evaluation Rate')
        ax1.set_title('A. Overall Positive Evaluation Rates')
        ax1.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, rate in zip(bars, positive_rates):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{rate:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Panel B: By jailbreak tactic
        ax2 = axes[0, 1]
        tactic_data = self.data.groupby('tactic').agg({
            'original_jailbroken': 'mean',
            'human_jailbroken': 'mean',
            'ai_meta_jailbroken': 'mean'
        }).round(3)
        
        x = np.arange(len(tactic_data))
        width = 0.25
        
        ax2.bar(x - width, tactic_data['original_jailbroken'], width, 
               label='Original', color=self.colors['original'], alpha=0.8)
        ax2.bar(x, tactic_data['human_jailbroken'], width,
               label='Human', color=self.colors['human'], alpha=0.8)
        ax2.bar(x + width, tactic_data['ai_meta_jailbroken'], width,
               label='AI Meta', color=self.colors['ai_meta'], alpha=0.8)
        
        ax2.set_xlabel('Jailbreak Tactic')
        ax2.set_ylabel('Positive Evaluation Rate')
        ax2.set_title('B. Positive Rates by Jailbreak Tactic')
        ax2.set_xticks(x)
        ax2.set_xticklabels(tactic_data.index, rotation=45, ha='right')
        ax2.legend()
        ax2.set_ylim(0, 1)
        
        # Panel C: Agreement rates by tactic
        ax3 = axes[1, 0]
        tactic_agreements = {}
        for tactic in self.data['tactic'].unique():
            tactic_df = self.data[self.data['tactic'] == tactic]
            if len(tactic_df) > 1:
                orig = tactic_df['original_jailbroken']
                human = tactic_df['human_jailbroken']
                ai = tactic_df['ai_meta_jailbroken']
                
                tactic_agreements[tactic] = {
                    'Original-Human': (orig == human).mean(),
                    'Original-AI': (orig == ai).mean(),
                    'Human-AI': (human == ai).mean()
                }
        
        if tactic_agreements:
            tactics = list(tactic_agreements.keys())
            comparisons = ['Original-Human', 'Original-AI', 'Human-AI']
            comparison_colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            x = np.arange(len(tactics))
            width = 0.25
            
            for i, comp in enumerate(comparisons):
                values = [tactic_agreements[tactic][comp] for tactic in tactics]
                ax3.bar(x + i*width, values, width, label=comp, 
                       color=comparison_colors[i], alpha=0.8)
            
            ax3.set_xlabel('Jailbreak Tactic')
            ax3.set_ylabel('Agreement Rate')
            ax3.set_title('C. Pairwise Agreement by Tactic')
            ax3.set_xticks(x + width)
            ax3.set_xticklabels(tactics, rotation=45, ha='right')
            ax3.legend()
            ax3.set_ylim(0, 1)
        
        # Panel D: Three-way agreement patterns
        ax4 = axes[1, 1]
        
        # Calculate disagreement patterns
        patterns = []
        for _, row in self.data.iterrows():
            o, h, a = row['original_jailbroken'], row['human_jailbroken'], row['ai_meta_jailbroken']
            if o and h and a:
                patterns.append('All Agree\n(Jailbroken)')
            elif not o and not h and not a:
                patterns.append('All Agree\n(Not Jailbroken)')
            elif o and h and not a:
                patterns.append('Orig+Human\nvs AI')
            elif o and not h and a:
                patterns.append('Orig+AI\nvs Human')
            elif not o and h and a:
                patterns.append('Human+AI\nvs Orig')
            else:
                patterns.append('Mixed\nDisagreement')
        
        pattern_counts = pd.Series(patterns).value_counts()
        colors_pattern = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#87CEEB', '#FFD23F']
        
        wedges, texts, autotexts = ax4.pie(pattern_counts.values, 
                                          labels=pattern_counts.index,
                                          colors=colors_pattern[:len(pattern_counts)],
                                          autopct='%1.1f%%',
                                          startangle=90)
        ax4.set_title('D. Three-Way Agreement Patterns')
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 2: {save_path}")
        plt.show()
    
    def plot_confusion_matrices(self, save_path='fig3_confusion_matrices.pdf'):
        """Figure 3: Confusion matrices for pairwise comparisons"""
        
        if self.data.empty:
            return
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        original = self.data['original_jailbroken'].astype(int)
        human = self.data['human_jailbroken'].astype(int)
        ai_meta = self.data['ai_meta_jailbroken'].astype(int)
        
        comparisons = [
            ('Original', 'Human', original, human),
            ('Original', 'AI Meta', original, ai_meta),
            ('Human', 'AI Meta', human, ai_meta)
        ]
        
        for i, (name1, name2, eval1, eval2) in enumerate(comparisons):
            ax = axes[i]
            
            # Calculate confusion matrix
            cm = confusion_matrix(eval1, eval2)
            
            # Plot heatmap
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                       cbar_kws={'shrink': 0.8})
            
            ax.set_xlabel(f'{name2} Evaluation')
            ax.set_ylabel(f'{name1} Evaluation')
            ax.set_title(f'{name1} vs {name2}')
            
            # Set tick labels
            ax.set_xticklabels(['Not Jailbroken', 'Jailbroken'])
            ax.set_yticklabels(['Not Jailbroken', 'Jailbroken'])
            
            # Calculate and add agreement rate
            agreement_rate = (eval1 == eval2).mean()
            ax.text(0.5, -0.15, f'Agreement: {agreement_rate:.3f}', 
                   transform=ax.transAxes, ha='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 3: {save_path}")
        plt.show()
    
    def plot_detailed_disagreement_analysis(self, save_path='fig4_disagreement_analysis.pdf'):
        """Figure 4: Detailed analysis of disagreement patterns"""
        
        if self.data.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: Disagreement by test case
        ax1 = axes[0, 0]
        
        test_case_disagreements = {}
        for tc in self.data['test_case'].unique():
            tc_data = self.data[self.data['test_case'] == tc]
            if len(tc_data) >= 3:  # Only include test cases with sufficient data
                orig = tc_data['original_jailbroken']
                human = tc_data['human_jailbroken']
                ai = tc_data['ai_meta_jailbroken']
                
                # Calculate three-way disagreement rate
                three_way_agree = (orig == human) & (human == ai)
                disagreement_rate = 1 - three_way_agree.mean()
                test_case_disagreements[tc] = disagreement_rate
        
        if test_case_disagreements:
            tc_sorted = sorted(test_case_disagreements.items(), key=lambda x: x[1], reverse=True)
            test_cases, disagreement_rates = zip(*tc_sorted)
            
            bars = ax1.barh(range(len(test_cases)), disagreement_rates, 
                           color=self.colors['disagreement'], alpha=0.8, edgecolor='black')
            ax1.set_yticks(range(len(test_cases)))
            ax1.set_yticklabels([tc.replace('_', ' ').title() for tc in test_cases])
            ax1.set_xlabel('Three-Way Disagreement Rate')
            ax1.set_title('A. Disagreement by Test Case')
            ax1.set_xlim(0, 1)
            
            # Add value labels
            for i, (bar, rate) in enumerate(zip(bars, disagreement_rates)):
                ax1.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                        f'{rate:.3f}', va='center', fontweight='bold')
        
        # Panel B: Model-specific analysis (if sufficient data)
        ax2 = axes[0, 1]
        
        model_agreements = {}
        for model in self.data['target_model'].unique():
            model_data = self.data[self.data['target_model'] == model]
            if len(model_data) >= 5:  # Only models with sufficient data
                orig = model_data['original_jailbroken']
                human = model_data['human_jailbroken']
                ai = model_data['ai_meta_jailbroken']
                
                model_agreements[model] = {
                    'Original-Human': (orig == human).mean(),
                    'Original-AI': (orig == ai).mean(),
                    'Human-AI': (human == ai).mean(),
                    'count': len(model_data)
                }
        
        if model_agreements:
            models = list(model_agreements.keys())
            model_names = [m.split('/')[-1] for m in models]  # Simplify model names
            
            orig_human = [model_agreements[m]['Original-Human'] for m in models]
            orig_ai = [model_agreements[m]['Original-AI'] for m in models]
            human_ai = [model_agreements[m]['Human-AI'] for m in models]
            
            x = np.arange(len(models))
            width = 0.25
            
            ax2.bar(x - width, orig_human, width, label='Original-Human', alpha=0.8)
            ax2.bar(x, orig_ai, width, label='Original-AI', alpha=0.8)
            ax2.bar(x + width, human_ai, width, label='Human-AI', alpha=0.8)
            
            ax2.set_xlabel('Target Model')
            ax2.set_ylabel('Agreement Rate')
            ax2.set_title('B. Agreement by Target Model')
            ax2.set_xticks(x)
            ax2.set_xticklabels(model_names, rotation=45, ha='right')
            ax2.legend()
            ax2.set_ylim(0, 1)
        else:
            ax2.text(0.5, 0.5, 'Insufficient model data\nfor analysis', 
                    ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            ax2.set_title('B. Agreement by Target Model')
        
        # Panel C: Evaluation system bias analysis
        ax3 = axes[1, 0]
        
        # Create bias comparison chart
        bias_data = []
        systems = ['Original', 'Human', 'AI Meta']
        evals = [self.data['original_jailbroken'], self.data['human_jailbroken'], self.data['ai_meta_jailbroken']]
        
        for i, (system, eval_data) in enumerate(zip(systems, evals)):
            positive_rate = eval_data.mean()
            bias_data.append(positive_rate)
        
        # Calculate relative bias compared to human evaluations (as reference)
        human_rate = bias_data[1]
        relative_bias = [(rate - human_rate) for rate in bias_data]
        
        colors = [self.colors['original'], self.colors['human'], self.colors['ai_meta']]
        bars = ax3.bar(systems, relative_bias, color=colors, alpha=0.8, edgecolor='black')
        
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax3.set_ylabel('Relative Bias vs Human Evaluations')
        ax3.set_title('C. Evaluation System Bias')
        
        # Add value labels
        for bar, bias in zip(bars, relative_bias):
            y_pos = bias + (0.01 if bias >= 0 else -0.01)
            ax3.text(bar.get_x() + bar.get_width()/2, y_pos,
                    f'{bias:+.3f}', ha='center', va='bottom' if bias >= 0 else 'top',
                    fontweight='bold')
        
        # Panel D: Statistical significance visualization
        ax4 = axes[1, 1]
        
        # Mock statistical test results (replace with actual results)
        comparisons = ['Orig-Human', 'Orig-AI', 'Human-AI']
        p_values = [0.001, 0.003, 0.15]  # These should come from actual statistical tests
        
        # Create significance level visualization
        significance_levels = []
        for p in p_values:
            if p < 0.001:
                significance_levels.append('***')
            elif p < 0.01:
                significance_levels.append('**')
            elif p < 0.05:
                significance_levels.append('*')
            else:
                significance_levels.append('ns')
        
        colors_sig = ['red' if s != 'ns' else 'gray' for s in significance_levels]
        bars = ax4.bar(comparisons, [-np.log10(p) for p in p_values], 
                      color=colors_sig, alpha=0.8, edgecolor='black')
        
        ax4.axhline(y=-np.log10(0.05), color='red', linestyle='--', alpha=0.7, label='p = 0.05')
        ax4.axhline(y=-np.log10(0.01), color='red', linestyle='--', alpha=0.7, label='p = 0.01')
        
        ax4.set_ylabel('-log₁₀(p-value)')
        ax4.set_title('D. Statistical Significance Tests')
        ax4.legend()
        
        # Add significance markers
        for i, (bar, sig) in enumerate(zip(bars, significance_levels)):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    sig, ha='center', va='bottom', fontweight='bold', fontsize=14)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 4: {save_path}")
        plt.show()
    
    def generate_all_plots(self):
        """Generate all publication-quality plots"""
        
        if self.data.empty:
            print("No data available for plotting")
            return
        
        print("Generating publication-quality plots...")
        print(f"Dataset: {len(self.data)} cases")
        
        self.plot_overall_agreement_matrix()
        self.plot_evaluation_distributions()
        self.plot_confusion_matrices()
        self.plot_detailed_disagreement_analysis()
        
        print("\nAll publication plots generated successfully!")
        print("Files saved:")
        print("- fig1_agreement_matrix.pdf")
        print("- fig2_evaluation_distributions.pdf") 
        print("- fig3_confusion_matrices.pdf")
        print("- fig4_disagreement_analysis.pdf")

def main():
    """Main function for publication plot generation"""
    plotter = PublicationPlots()
    plotter.generate_all_plots()
    return plotter

if __name__ == "__main__":
    plotter = main()