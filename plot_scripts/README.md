# Plot Scripts

This directory contains scripts for generating various visualizations from the CSV results of jailbreak experiments.

## Script Overview

## Workflow

1. First, run `create_csv.py` to generate the consolidated CSV file from raw results
2. Then, use `plot_main_graphs_from_csv.py` to create visualizations from the CSV file


### `create_csv.py`

This script is used to create a CSV file from the raw experiment results. It should be run before using `plot_main_graphs_from_csv.py`.

The script:
1. Reads raw experiment results from the `results` directory
2. Processes and combines the data from multiple experiments
3. Calculates success metrics and scores
4. Outputs a consolidated CSV file to the `csv_results` directory

### Usage

```bash
python create_csv.py [--input_dir <path>] [--output_dir <path>]
```

Arguments:
- `--input_dir`: (Optional) Directory containing raw experiment results (default: ../results)
- `--output_dir`: (Optional) Directory for output CSV file (default: ../csv_results)

Example:
```bash
python create_csv.py --input_dir ../results --output_dir ../csv_results
```

### `plot_main_graphs_from_csv.py`

This is the main script for generating all the plots from a CSV file containing experiment results. It creates several different visualizations:

1. Best Score Split-Cell Heatmap (`best_score_heatmap_from_*.png`)
   - Shows the best score achieved for each tactic/test case combination
   - Split-cell visualization comparing multi-turn vs single-turn results
   - Each cell shows both multi-turn (M:) and single-turn (S:) scores

2. Success Rate/Best Score Split-Cell Heatmap (`success_by_tactic_test_from_*_[metric].png`)
   - Shows either success rates (based on threshold) or best scores for each tactic/test case
   - Split-cell visualization comparing multi-turn vs single-turn results
   - Each cell shows both multi-turn (M:) and single-turn (S:) values
   - Metric suffix indicates whether success_rate or best_score was used

3. Individual Success Rate/Best Score Heatmaps
   - Multi-turn version (`success_by_tactic_test(multi)_from_*_v{1,2}_[metric].png`)
   - Single-turn version (`success_by_tactic_test(single)_from_*_v{1,2}_[metric].png`)
   - Two versions available (v1 and v2) with different styling
   - v1: Traditional heatmap with averages
   - v2: Modern bar-based visualization with larger text
   - Metric suffix indicates whether success_rate or best_score was used

4. Model Size Analysis
   - Line plot (`success_rate_by_model_size_from_*_[metric].png`)
   - Shows success rate vs model size for both turn types
   - Logarithmic x-axis for model size
   - Special handling for GPT-4o-mini model (shown as triangles)
   - Includes error bars and sample sizes

5. Model Name Analysis
   - Bar plot (`success_rate_by_model_name_from_*_[metric].png`)
   - Shows success rates by model name, ordered by model size
   - Side-by-side comparison of multi-turn vs single-turn results
   - Includes error bars and sample sizes
   - Model parameter sizes shown below names

### Usage

```bash
python plot_main_graphs_from_csv.py --csv <csv_filename> [--version <1|2>] [--threshold <float>] [--metric <success_rate|best_score>] [--target-model <model_name>]
```

Arguments:
- `--csv`: (Required) Name of the CSV file in the csv_results directory
- `--version`: (Optional) Version of the plot style (1 or 2, default=1)
- `--threshold`: (Optional) Score threshold (0-1.0) for success determination (default=1.0). Only used when metric='success_rate'
- `--metric`: (Optional) Metric to use for analysis: 'success_rate' (binary threshold) or 'best_score' (best score achieved). Default='success_rate'
- `--target-model`: (Optional) Target model to filter data (e.g., "meta-llama/llama-3.1-70b-instruct")

Example:
```bash
# Using success rate metric with threshold
python plot_main_graphs_from_csv.py --csv results_2024_03_20.csv --version 2 --threshold 0.5 --metric success_rate

# Using best score metric (threshold not used)
python plot_main_graphs_from_csv.py --csv results_2024_03_20.csv --version 2 --metric best_score

# Filtering for specific model
python plot_main_graphs_from_csv.py --csv results_2024_03_20.csv --target-model meta-llama/llama-3.1-70b-instruct
```

## Output Directory Structure

The scripts will create a `plot_outputs` directory in the project root if it doesn't exist. All generated plots will be saved there with filenames based on the input CSV filename and the selected metric.

## Notes

- The scripts assume the CSV file is located in the `csv_results` directory
- All plots are generated with high resolution (300 DPI)
- The scripts handle both multi-turn and single-turn data automatically
- Model sizes are defined in the script for known models:
  - GPT-4o-mini: 8B parameters
  - Llama 3.1 8B: 8B parameters
  - Llama 3.1 70B: 70B parameters
  - Llama 3.1 405B: 405B parameters
  - Llama 3.2 1B: 1B parameters
  - Llama 3.2 3B: 3B parameters
  - Llama 3.3 70B: 70B parameters
- When using the 'success_rate' metric, success is determined by whether the minimum score is less than or equal to the threshold (0-1.0)
- When using the 'best_score' metric, the actual best score achieved is shown (threshold is ignored)
- The threshold is specified as a value between 0 and 1.0 where higher is better
- All plots include error bars and sample sizes where applicable 