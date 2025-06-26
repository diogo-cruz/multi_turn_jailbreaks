import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import ast

# Load the data
df = pd.read_csv('/home/dcruz/multi_turn_jailbreaks/csv_results/master_results.csv')

# Filter for batch3A rows
batch3a_df = df[df['batch'] == 'batch3A'].copy()

print(f"Total rows in dataset: {len(df)}")
print(f"Batch3A rows: {len(batch3a_df)}")

# Parse the scores column to extract score lists
def parse_scores(scores_str):
    """Parse the scores string into a list of floats"""
    try:
        if pd.isna(scores_str) or scores_str == '[]':
            return []
        # Handle string representation of list
        if isinstance(scores_str, str):
            return ast.literal_eval(scores_str)
        return scores_str
    except:
        return []

batch3a_df['score_list'] = batch3a_df['scores'].apply(parse_scores)

# Filter for rows with at least 2 rounds (consecutive pairs possible)
multi_round_df = batch3a_df[batch3a_df['score_list'].apply(lambda x: len(x) >= 2)].copy()

print(f"Rows with at least 2 rounds: {len(multi_round_df)}")

# Extract consecutive round pairs and calculate correlations
max_rounds = 8
correlations = {}
scatter_data = {}

for i in range(max_rounds - 1):  # 0 to 6 (rounds 1-2, 2-3, ..., 7-8)
    round_i = i
    round_j = i + 1
    
    # Collect pairs where both rounds exist
    pairs_i = []
    pairs_j = []
    
    for _, row in multi_round_df.iterrows():
        scores = row['score_list']
        if len(scores) > round_j:  # Both rounds exist
            pairs_i.append(scores[round_i])
            pairs_j.append(scores[round_j])
    
    if len(pairs_i) >= 3:  # Need at least 3 points for meaningful correlation
        correlation, p_value = pearsonr(pairs_i, pairs_j)
        correlations[f'Round {round_i+1} vs Round {round_j+1}'] = {
            'correlation': correlation,
            'p_value': p_value,
            'n_pairs': len(pairs_i)
        }
        scatter_data[f'Round {round_i+1} vs Round {round_j+1}'] = {
            'x': pairs_i,
            'y': pairs_j
        }
        print(f"Round {round_i+1} vs Round {round_j+1}: r={correlation:.3f}, p={p_value:.3f}, n={len(pairs_i)}")

# Create the 3x3 grid plot
fig, axes = plt.subplots(3, 3, figsize=(15, 15))
fig.suptitle('Score Correlations Between Consecutive Rounds (Batch3A)', fontsize=16, y=0.98)

plot_idx = 0
for i in range(3):
    for j in range(3):
        ax = axes[i, j]
        
        if plot_idx < len(scatter_data):
            # Get the data for this plot
            round_pair = list(scatter_data.keys())[plot_idx]
            data = scatter_data[round_pair]
            corr_info = correlations[round_pair]
            
            # Create scatter plot with point sizes proportional to frequency
            from collections import Counter
            
            # Count frequency of each (x, y) pair
            coord_pairs = list(zip(data['x'], data['y']))
            coord_counts = Counter(coord_pairs)
            
            # Extract unique coordinates and their counts
            unique_x = [coord[0] for coord in coord_counts.keys()]
            unique_y = [coord[1] for coord in coord_counts.keys()]
            counts = list(coord_counts.values())
            
            # Scale point sizes (base size 20, scaled by count)
            point_sizes = [20 + 80 * (count - 1) / max(1, max(counts) - 1) for count in counts]
            
            ax.scatter(unique_x, unique_y, alpha=0.6, s=point_sizes, c='blue', edgecolors='black', linewidth=0.5)
            
            # Add regression line
            if len(data['x']) > 1:
                z = np.polyfit(data['x'], data['y'], 1)
                p = np.poly1d(z)
                x_line = np.linspace(min(data['x']), max(data['x']), 100)
                ax.plot(x_line, p(x_line), "r--", alpha=0.8)
            
            # Set labels and title
            ax.set_xlabel(f'Score at Round {plot_idx+1}')
            ax.set_ylabel(f'Score at Round {plot_idx+2}')
            ax.set_title(f'{round_pair}\nr={corr_info["correlation"]:.3f}, n={corr_info["n_pairs"]}')
            
            # Set axis limits
            ax.set_xlim(-0.1, 1.1)
            ax.set_ylim(-0.1, 1.1)
            ax.grid(True, alpha=0.3)
            
        else:
            # Empty subplot
            ax.set_visible(False)
        
        plot_idx += 1

# Add a legend explaining point sizes
legend_elements = [
    plt.scatter([], [], s=20, c='blue', alpha=0.6, edgecolors='black', linewidth=0.5, label='1 point'),
    plt.scatter([], [], s=60, c='blue', alpha=0.6, edgecolors='black', linewidth=0.5, label='Multiple points'),
    plt.scatter([], [], s=100, c='blue', alpha=0.6, edgecolors='black', linewidth=0.5, label='Many points')
]
fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.95), 
          title='Point size = frequency')

plt.tight_layout()
plt.savefig('/home/dcruz/multi_turn_jailbreaks/consecutive_rounds_correlation_analysis.png', 
           dpi=300, bbox_inches='tight')
plt.show()

# Print summary statistics
print("\n=== CORRELATION SUMMARY ===")
for round_pair, info in correlations.items():
    print(f"{round_pair}: r={info['correlation']:.3f}, p={info['p_value']:.3f}, n={info['n_pairs']}")

# Also create a summary table
summary_df = pd.DataFrame([
    {
        'Round_Pair': round_pair,
        'Correlation': info['correlation'],
        'P_Value': info['p_value'],
        'N_Pairs': info['n_pairs']
    }
    for round_pair, info in correlations.items()
])

print("\n=== SUMMARY TABLE ===")
print(summary_df.to_string(index=False))

# Save summary to CSV
summary_df.to_csv('/home/dcruz/multi_turn_jailbreaks/consecutive_rounds_correlation_summary.csv', index=False)
print(f"\nSummary saved to consecutive_rounds_correlation_summary.csv")