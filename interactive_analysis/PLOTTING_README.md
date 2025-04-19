# Python Plotting Implementation for Jailbreak Testing Analysis

This directory contains Python scripts to generate static plots from the jailbreak testing data. While the interactive visualization provides dynamic exploration, these scripts create high-quality PNG and PDF exports of all the visualizations for use in reports, papers, or presentations.

## Available Scripts

- **generate_all_plots.py**: Main script that runs all the plotting scripts and outputs a summary
- **generate_plots.py**: Creates bar charts, line charts and general data visualizations
- **generate_heatmaps.py**: Creates heatmap visualizations for ASR, refusal counts, and round counts
- **generate_scatter_plots.py**: Creates scatter plots showing ASR vs. model size and ASR vs. release date

## Usage

To generate all plots at once, run:

```bash
python generate_all_plots.py
```

This will:
1. Create a `figures/` directory (if it doesn't exist)
2. Run all plotting scripts
3. Save PNG and PDF versions of each visualization
4. Display a summary of the generated files

Alternatively, you can run individual scripts:

```bash
python generate_plots.py      # Basic plots only
python generate_heatmaps.py   # Heatmaps only
python generate_scatter_plots.py  # Scatter plots only
```

## Plot Types

The scripts generate the following types of visualizations:

1. **Model Analysis**
   - Success rates per model
   - Refusal counts per model
   - Round counts per model

2. **Test Case Analysis**
   - Success rates per test case
   - Test case performance across model sizes
   - Error bars showing variation

3. **Tactic Analysis**
   - Success rates per jailbreak tactic
   - Tactic effectiveness across model sizes
   - Separate analysis for multi-turn vs. single-turn approaches

4. **Heatmaps**
   - ASR (Attack Success Rate) heatmaps
   - Refusal count heatmaps
   - Round count heatmaps
   - Model vs. test case comparison heatmaps

5. **Size and Release Date Analysis**
   - ASR vs. Model Size scatter plot (color-coded by company)
   - ASR vs. Release Date scatter plot (color-coded by company)

## Data Sources

The scripts process the same CSV files as the interactive visualization:

- **results_test_runs.csv**: Initial test runs data
- **results_2D.csv**: Evaluated using Anthropic Claude 3 Haiku
- **results_2D_2.csv**: Evaluated using OpenAI GPT-4.1-mini
- **results_2B.csv**: Evaluated using GPT-4o-mini-2024-07-18
- **results_final_3samples.csv**: Final results with 3 samples per configuration
- **enhanced_master_data.csv**: Merged dataset from all source files
- **model_comparison.csv**: Model metadata (size, company, release date)

## Dependencies

- Python 3.6+
- pandas
- numpy
- matplotlib
- seaborn

## Output Format

All visualizations are saved in both PNG (300 dpi) and PDF formats in the `figures/` directory. The filename pattern is:

```
[data_source]_[plot_type].[extension]
```

For example:
- `enhanced_master_data_asr_vs_size.png`
- `results_2B_heatmap.pdf`
- `results_final_3samples_model_success.png`

## Customization

You can customize the plots by modifying the following aspects in the script files:

- Figure sizes
- Color schemes
- Text formatting
- Plot titles and labels
- Output resolution

## Replication Notes

These scripts replicate the same visualizations available in the interactive React-based visualization, but as static outputs for ease of sharing and including in documentation. Both versions use the same underlying data and analytical approach. 