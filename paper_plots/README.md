# Paper Plots

This directory contains scripts to generate plots for the research paper on multi-turn jailbreak attacks.

## Directory Structure

```
paper_plots/
├── src/                                    # Source scripts
│   ├── plot_asr_vs_model_size.py          # ASR vs model size
│   ├── plot_asr_vs_release_date.py        # ASR vs release date  
│   ├── plot_asr_vs_reasoning.py           # ASR vs reasoning effort
│   ├── plot_asr_vs_tactics.py             # ASR vs tactics (bar plot)
│   └── generate_all_plots.py              # Run all plots
├── plots/                                  # Generated plots (PDF/PNG)
└── README.md                              # This file
```

## Data Sources

The scripts read data from:
- `csv_results/master_results.csv` - Experimental results data
- `model_comparison.csv` - Model information (size, release date, etc.)

## Plot Descriptions

### 1. ASR vs Model Size (`plot_asr_vs_model_size.py`)
- **Description**: Attack Success Rate vs model size in parameters
- **Features**: 
  - Multi-turn (solid lines) and single-turn (dashed lines)
  - Different colors for model families (DeepSeek, Google, Meta, etc.)
  - Log scale for x-axis if parameter range is large
- **Output**: `asr_vs_model_size.pdf/png`

### 2. ASR vs Release Date (`plot_asr_vs_release_date.py`)  
- **Description**: Attack Success Rate vs model release date
- **Features**:
  - Multi-turn (solid lines) and single-turn (dashed lines)
  - Different colors for model families
  - Time series format with proper date formatting
- **Output**: `asr_vs_release_date.pdf/png`

### 3. ASR vs Reasoning Effort (`plot_asr_vs_reasoning.py`)
- **Description**: Attack Success Rate vs reasoning level (low/medium/high)
- **Features**:
  - Separate subplots for multi-turn and single-turn
  - Combined plot with both turn types
  - Only includes data where reasoning level is specified
- **Output**: `asr_vs_reasoning.pdf/png`, `asr_vs_reasoning_combined.pdf/png`

### 4. ASR vs Tactics (`plot_asr_vs_tactics.py`)
- **Description**: Bar plot of Attack Success Rate by jailbreak tactic
- **Features**:
  - Averaged over all models
  - Side-by-side bars for multi-turn and single-turn
  - Both vertical and horizontal bar chart versions
  - Value labels on bars
- **Output**: `asr_vs_tactics.pdf/png`, `asr_vs_tactics_horizontal.pdf/png`

## Requirements

The scripts require the following Python packages:
- pandas
- matplotlib
- numpy
- python-dateutil

LaTeX support must be available for matplotlib (for publication-quality fonts).

## Usage

### Run All Plots
```bash
cd paper_plots/src
python generate_all_plots.py
```

The script automatically detects all Python files starting with `plot_` in the `src/` directory, making it future-proof for additional plotting scripts.

### Run Individual Plots
```bash
cd paper_plots/src
python plot_asr_vs_model_size.py
python plot_asr_vs_release_date.py
python plot_asr_vs_reasoning.py
python plot_asr_vs_tactics.py
```

## Plot Specifications

- **Font**: LaTeX serif font (for publication quality)
- **Colors**: Default matplotlib color palette (tab10)
- **Format**: Both PDF (vector) and PNG (raster) versions
- **DPI**: 300 for high-quality output
- **ASR Definition**: Attack Success Rate = maximum over tactics, average over test cases, temperature 0

## Notes

- All scripts assume they are run from the `src/` directory
- Data paths are relative: `../../csv_results/master_results.csv` and `../../model_comparison.csv`
- Plots are saved to `../plots/` directory (automatically created)
- Model family classification is based on model name patterns
- Missing or unspecified data is handled gracefully
- Scripts use flexible model name matching without hardcoded data
- See `human_TODO.md` for information about missing model data that affects plot coverage

## Troubleshooting

### LaTeX Errors
If you encounter LaTeX-related errors, you can disable LaTeX rendering by commenting out these lines in each script:
```python
# plt.rcParams.update({
#     'text.usetex': True,
#     'font.family': 'serif',
#     'font.size': 12
# })
```

### Missing Data
If certain models don't appear in plots:
1. Check `human_TODO.md` for list of missing models in `model_comparison.csv`
2. Verify model names match between `master_results.csv` and `model_comparison.csv`
3. Check that required columns (Parameters, Release Date) are not null
4. Review data filtering criteria (temperature, reasoning levels, etc.)

### Dependencies
Install missing packages:
```bash
pip install pandas matplotlib numpy python-dateutil
``` 