#!/usr/bin/env python3
"""
Publication-Quality Visualization Suite for Three-Way Evaluation System Analysis by Turn Type

Generates publication-ready plots comparing Original, Human, and AI Meta-evaluation systems
with separate analysis for single-turn vs multi-turn cases.
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

class PublicationPlotsByTurns:
    """Publication-quality plotting suite for evaluation system analysis by turn type"""
    
    def __init__(self):
        self.load_data()
        self.colors = {
            'original': '#2E86AB',    # Blue
            'human': '#A23B72',       # Purple
            'ai_meta': '#F18F01',     # Orange
            'single_turn': '#2E86AB', # Blue for single-turn
            'multi_turn': '#C73E1D',  # Red for multi-turn
            'agreement': '#C73E1D',   # Red
            'disagreement': '#87CEEB' # Light blue
        }
        
    def load_data(self):
        """Load the three-way comparison dataset with turn type separation"""
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
            
            # Extract turn type from filename
            self.data['turn_type'] = self.data['filename'].apply(self.extract_turn_type)
            
            # Split by turn type
            self.single_turn_data = self.data[self.data['turn_type'] == 'single_turn'].copy()
            self.multi_turn_data = self.data[self.data['turn_type'] == 'multi_turn'].copy()
            
            print(f"Loaded {len(self.data)} cases for publication plots")
            print(f"Single-turn: {len(self.single_turn_data)}, Multi-turn: {len(self.multi_turn_data)}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
            self.single_turn_data = pd.DataFrame()
            self.multi_turn_data = pd.DataFrame()
    
    def extract_turn_type(self, filename):
        """Extract turn type from filename"""
        if 'single_turn' in filename:
            return 'single_turn'
        elif 'multi_turn' in filename:
            return 'multi_turn'
        else:
            return 'unknown'
    
    def plot_turn_type_comparison(self, save_path='fig1_turn_type_comparison.pdf'):
        """Figure 1: Overall comparison between single-turn and multi-turn cases"""
        
        if self.data.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: Agreement rates comparison
        ax1 = axes[0, 0]
        
        # Calculate agreement rates for both turn types
        def calc_agreements(df):
            if df.empty:
                return [0, 0, 0]
            original = df['original_jailbroken']
            human = df['human_jailbroken']
            ai_meta = df['ai_meta_jailbroken']
            return [
                (original == human).mean(),
                (original == ai_meta).mean(),
                (human == ai_meta).mean()
            ]
        
        single_agreements = calc_agreements(self.single_turn_data)
        multi_agreements = calc_agreements(self.multi_turn_data)
        
        x = np.arange(3)
        width = 0.35
        
        labels = ['Original-Human', 'Original-AI', 'Human-AI']
        
        ax1.bar(x - width/2, single_agreements, width, label='Single-turn', 
               color=self.colors['single_turn'], alpha=0.8)
        ax1.bar(x + width/2, multi_agreements, width, label='Multi-turn',
               color=self.colors['multi_turn'], alpha=0.8)
        
        ax1.set_xlabel('Evaluation System Pairs')
        ax1.set_ylabel('Agreement Rate')
        ax1.set_title('A. Agreement Rates by Turn Type')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.legend()
        ax1.set_ylim(0, 1)
        
        # Add value labels
        for i, (single_val, multi_val) in enumerate(zip(single_agreements, multi_agreements)):
            ax1.text(i - width/2, single_val + 0.02, f'{single_val:.3f}', 
                    ha='center', va='bottom', fontsize=10)
            ax1.text(i + width/2, multi_val + 0.02, f'{multi_val:.3f}', 
                    ha='center', va='bottom', fontsize=10)
        
        # Panel B: Positive evaluation rates
        ax2 = axes[0, 1]
        
        def calc_positive_rates(df):
            if df.empty:
                return [0, 0, 0]
            return [
                df['original_jailbroken'].mean(),
                df['human_jailbroken'].mean(),
                df['ai_meta_jailbroken'].mean()
            ]
        
        single_rates = calc_positive_rates(self.single_turn_data)
        multi_rates = calc_positive_rates(self.multi_turn_data)
        
        system_labels = ['Original', 'Human', 'AI Meta']
        
        ax2.bar(x - width/2, single_rates, width, label='Single-turn',
               color=self.colors['single_turn'], alpha=0.8)
        ax2.bar(x + width/2, multi_rates, width, label='Multi-turn',
               color=self.colors['multi_turn'], alpha=0.8)
        
        ax2.set_xlabel('Evaluation Systems')
        ax2.set_ylabel('Positive Evaluation Rate')
        ax2.set_title('B. Positive Rates by Turn Type')
        ax2.set_xticks(x)
        ax2.set_xticklabels(system_labels)
        ax2.legend()
        ax2.set_ylim(0, 1)
        
        # Panel C: Agreement by tactic for single-turn
        ax3 = axes[1, 0]
        
        if not self.single_turn_data.empty:
            single_tactic_data = []
            tactics = []
            for tactic in self.single_turn_data['tactic'].unique():
                tactic_df = self.single_turn_data[self.single_turn_data['tactic'] == tactic]
                if len(tactic_df) >= 3:  # Only include tactics with sufficient data
                    orig = tactic_df['original_jailbroken']
                    human = tactic_df['human_jailbroken']
                    ai = tactic_df['ai_meta_jailbroken']
                    
                    agreements = [
                        (orig == human).mean(),
                        (orig == ai).mean(),
                        (human == ai).mean()
                    ]
                    single_tactic_data.append(agreements)
                    tactics.append(tactic)
            
            if single_tactic_data:
                single_tactic_data = np.array(single_tactic_data)
                x_tactic = np.arange(len(tactics))
                width_tactic = 0.25
                
                ax3.bar(x_tactic - width_tactic, single_tactic_data[:, 0], width_tactic, 
                       label='Orig-Human', alpha=0.8)
                ax3.bar(x_tactic, single_tactic_data[:, 1], width_tactic,
                       label='Orig-AI', alpha=0.8)
                ax3.bar(x_tactic + width_tactic, single_tactic_data[:, 2], width_tactic,
                       label='Human-AI', alpha=0.8)
                
                ax3.set_xlabel('Jailbreak Tactic')
                ax3.set_ylabel('Agreement Rate')
                ax3.set_title('C. Single-Turn Agreement by Tactic')
                ax3.set_xticks(x_tactic)
                ax3.set_xticklabels(tactics, rotation=45, ha='right')
                ax3.legend()
                ax3.set_ylim(0, 1)
        else:
            ax3.text(0.5, 0.5, 'No single-turn data', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('C. Single-Turn Agreement by Tactic')
        
        # Panel D: Agreement by tactic for multi-turn
        ax4 = axes[1, 1]
        
        if not self.multi_turn_data.empty:
            multi_tactic_data = []
            multi_tactics = []
            for tactic in self.multi_turn_data['tactic'].unique():
                tactic_df = self.multi_turn_data[self.multi_turn_data['tactic'] == tactic]
                if len(tactic_df) >= 3:
                    orig = tactic_df['original_jailbroken']
                    human = tactic_df['human_jailbroken']
                    ai = tactic_df['ai_meta_jailbroken']
                    
                    agreements = [
                        (orig == human).mean(),
                        (orig == ai).mean(),
                        (human == ai).mean()
                    ]
                    multi_tactic_data.append(agreements)
                    multi_tactics.append(tactic)
            
            if multi_tactic_data:
                multi_tactic_data = np.array(multi_tactic_data)
                x_tactic = np.arange(len(multi_tactics))
                width_tactic = 0.25
                
                ax4.bar(x_tactic - width_tactic, multi_tactic_data[:, 0], width_tactic,
                       label='Orig-Human', alpha=0.8)
                ax4.bar(x_tactic, multi_tactic_data[:, 1], width_tactic,
                       label='Orig-AI', alpha=0.8)
                ax4.bar(x_tactic + width_tactic, multi_tactic_data[:, 2], width_tactic,
                       label='Human-AI', alpha=0.8)
                
                ax4.set_xlabel('Jailbreak Tactic')
                ax4.set_ylabel('Agreement Rate')
                ax4.set_title('D. Multi-Turn Agreement by Tactic')
                ax4.set_xticks(x_tactic)
                ax4.set_xticklabels(multi_tactics, rotation=45, ha='right')
                ax4.legend()
                ax4.set_ylim(0, 1)
        else:
            ax4.text(0.5, 0.5, 'No multi-turn data', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('D. Multi-Turn Agreement by Tactic')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 1: {save_path}")
        plt.show()
    
    def plot_detailed_turn_analysis(self, save_path='fig2_detailed_turn_analysis.pdf'):
        """Figure 2: Detailed analysis comparing single-turn vs multi-turn performance"""
        
        if self.data.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Panel A: Three-way agreement patterns for single-turn
        ax1 = axes[0, 0]
        
        if not self.single_turn_data.empty:
            single_patterns = []
            for _, row in self.single_turn_data.iterrows():
                o, h, a = row['original_jailbroken'], row['human_jailbroken'], row['ai_meta_jailbroken']
                if o and h and a:
                    single_patterns.append('All Agree\n(Jailbroken)')
                elif not o and not h and not a:
                    single_patterns.append('All Agree\n(Not Jailbroken)')
                elif (o and h) and not a:
                    single_patterns.append('Orig+Human\nvs AI')
                elif (o and a) and not h:
                    single_patterns.append('Orig+AI\nvs Human')
                elif (h and a) and not o:
                    single_patterns.append('Human+AI\nvs Orig')
                else:
                    single_patterns.append('Mixed\nDisagreement')
            
            pattern_counts = pd.Series(single_patterns).value_counts()
            wedges, texts, autotexts = ax1.pie(pattern_counts.values, 
                                              labels=pattern_counts.index,
                                              autopct='%1.1f%%',
                                              startangle=90)
            ax1.set_title(f'A. Single-Turn Agreement Patterns\n(n={len(self.single_turn_data)})')
            
            for autotext in autotexts:
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
        else:
            ax1.text(0.5, 0.5, 'No single-turn data', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('A. Single-Turn Agreement Patterns')
        
        # Panel B: Three-way agreement patterns for multi-turn
        ax2 = axes[0, 1]
        
        if not self.multi_turn_data.empty:
            multi_patterns = []
            for _, row in self.multi_turn_data.iterrows():
                o, h, a = row['original_jailbroken'], row['human_jailbroken'], row['ai_meta_jailbroken']
                if o and h and a:
                    multi_patterns.append('All Agree\n(Jailbroken)')
                elif not o and not h and not a:
                    multi_patterns.append('All Agree\n(Not Jailbroken)')
                elif (o and h) and not a:
                    multi_patterns.append('Orig+Human\nvs AI')
                elif (o and a) and not h:
                    multi_patterns.append('Orig+AI\nvs Human')
                elif (h and a) and not o:
                    multi_patterns.append('Human+AI\nvs Orig')
                else:
                    multi_patterns.append('Mixed\nDisagreement')
            
            pattern_counts = pd.Series(multi_patterns).value_counts()
            wedges, texts, autotexts = ax2.pie(pattern_counts.values, 
                                              labels=pattern_counts.index,
                                              autopct='%1.1f%%',
                                              startangle=90)
            ax2.set_title(f'B. Multi-Turn Agreement Patterns\n(n={len(self.multi_turn_data)})')
            
            for autotext in autotexts:
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
        else:
            ax2.text(0.5, 0.5, 'No multi-turn data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('B. Multi-Turn Agreement Patterns')
        
        # Panel C: System bias comparison
        ax3 = axes[1, 0]
        
        def calc_bias_relative_to_human(df):
            if df.empty:
                return [0, 0, 0]
            human_rate = df['human_jailbroken'].mean()
            return [
                df['original_jailbroken'].mean() - human_rate,
                human_rate - human_rate,  # Always 0 for human (reference)
                df['ai_meta_jailbroken'].mean() - human_rate
            ]
        
        single_bias = calc_bias_relative_to_human(self.single_turn_data)
        multi_bias = calc_bias_relative_to_human(self.multi_turn_data)
        
        x = np.arange(3)
        width = 0.35
        systems = ['Original', 'Human', 'AI Meta']
        
        bars1 = ax3.bar(x - width/2, single_bias, width, label='Single-turn', alpha=0.8)
        bars2 = ax3.bar(x + width/2, multi_bias, width, label='Multi-turn', alpha=0.8)
        
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Evaluation System')
        ax3.set_ylabel('Bias Relative to Human Evaluations')
        ax3.set_title('C. System Bias Comparison')
        ax3.set_xticks(x)
        ax3.set_xticklabels(systems)
        ax3.legend()
        
        # Panel D: Case count distribution
        ax4 = axes[1, 1]
        
        # Count cases by tactic and turn type
        tactic_counts = self.data.groupby(['tactic', 'turn_type']).size().unstack(fill_value=0)
        
        if not tactic_counts.empty:
            tactic_counts.plot(kind='bar', ax=ax4, color=[self.colors['single_turn'], self.colors['multi_turn']], alpha=0.8)
            ax4.set_xlabel('Jailbreak Tactic')
            ax4.set_ylabel('Number of Cases')
            ax4.set_title('D. Case Distribution by Tactic and Turn Type')
            ax4.legend(['Single-turn', 'Multi-turn'])
            ax4.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for container in ax4.containers:
                ax4.bar_label(container, fontsize=9)
        else:
            ax4.text(0.5, 0.5, 'No tactic data available', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('D. Case Distribution by Tactic and Turn Type')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved Figure 2: {save_path}")
        plt.show()
    
    def generate_all_plots(self):
        """Generate all publication-quality plots with turn type analysis"""
        
        if self.data.empty:
            print("No data available for plotting")
            return
        
        print("Generating publication-quality plots with turn type analysis...")
        print(f"Dataset: {len(self.data)} cases ({len(self.single_turn_data)} single-turn, {len(self.multi_turn_data)} multi-turn)")
        
        self.plot_turn_type_comparison()
        self.plot_detailed_turn_analysis()
        
        print("\nAll publication plots by turn type generated successfully!")
        print("Files saved:")
        print("- fig1_turn_type_comparison.pdf")
        print("- fig2_detailed_turn_analysis.pdf")

def main():
    """Main function for publication plot generation by turn type"""
    plotter = PublicationPlotsByTurns()
    plotter.generate_all_plots()
    return plotter

if __name__ == "__main__":
    plotter = main()