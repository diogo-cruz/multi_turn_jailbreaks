# Interactive Analysis of Jailbreak Testing Results

This folder contains an interactive visualization tool for analyzing the results of jailbreak testing experiments across different language models, test cases, and tactics.

## Directory Structure

```
interactive_analysis/
├── README.md           # This file
├── setup.sh           # Setup script for installing dependencies
├── package.json       # Node.js package configuration
├── vite.config.js    # Vite configuration
├── visualization.jsx  # Main React component with visualizations
├── analysis.js       # Command-line analysis script
├── public/           # Static files directory
├── model_comparison.csv  # Model metadata (size, company, release date)
├── enhanced_master_data.csv # Enhanced data for additional visualizations
└── results_*.csv     # Data files with test results
```

## Features

The visualization includes several interactive views:

1. **Dataset Selection**
   - Choose between different CSV datasets for analysis
   - Supports: results_test_runs.csv, results_2D.csv, results_2D_2.csv, results_2B.csv, results_final_3samples.csv, enhanced_master_data.csv

2. **Model Analysis**
   - Test case success rates per model
   - Jailbreak tactic success rates
   - Model comparison charts

3. **Test Case vs Size**
   - Analysis of test case performance across model sizes
   - Error bars showing variation across tactics
   - Log-scale visualization of model parameters

4. **Tactic vs Size**
   - Analysis of tactic effectiveness across model sizes
   - Comparison of multi-turn vs single-turn approaches
   - Error bars showing variation across test cases

5. **Heatmaps**
   - ASR (Attack Success Rate) heatmaps
   - Refusal count heatmaps
   - Round count heatmaps
   - Separate views for multi-turn and single-turn approaches

6. **Enhanced Master Data Visualization**
   - ASR vs Model Size scatter plot (color-coded by company)
   - ASR vs Release Date scatter plot (color-coded by company)
   - Interactive tooltips showing detailed model information

## Data Sources

The tool supports multiple data sources with different evaluator models:

- **results_2D.csv**: Evaluated using Anthropic Claude 3 Haiku
- **results_2D_2.csv**: Evaluated using OpenAI GPT-4.1-mini 
- **results_2B.csv**: Evaluated using GPT-4o-mini-2024-07-18
- **results_test_runs.csv**: Evaluated using GPT-4o-mini-2024-07-18
- **results_final_3samples.csv**: Evaluated using GPT-4o-mini-2024-07-18
- **enhanced_master_data.csv**: Merged dataset created from all source files, preserving the original evaluator model for each dataset

## Setup Instructions

1. Run the setup script:
   ```bash
   ./setup.sh
   ```
   This will:
   - Install nvm (Node Version Manager)
   - Install Node.js v18 (LTS)
   - Install all required dependencies
   - Create necessary directories

2. After running the setup script:
   - Close and reopen your terminal
   - Run `nvm use 18` to ensure you're using the correct Node.js version
   - Run `npm start` to start the development server

3. Open your browser and navigate to:
   - http://localhost:3000 (default)
   - or http://localhost:3001 (if port 3000 is in use)

## Using the Command-Line Analysis Script

Besides the interactive visualization, you can also analyze CSV files using the command-line script:

```bash
# Run with default file (results_test_runs.csv)
node --experimental-modules analysis.js

# Run with a specific CSV file
node --experimental-modules analysis.js results_2B.csv
```

The script will output a summary of the analysis, including:
- Number of models in the dataset
- Test cases and tactics
- Example ASR values for test cases and tactics
- Common tactics across all models
- Overall model performance comparison

## Technical Details

- Built with React and Vite
- Uses Recharts for charts and visualizations
- Implements responsive design for various screen sizes
- CSV data processing with PapaParse
- Tailwind CSS for styling
- Node.js v18 (LTS) with nvm for version management

## Data Format

The visualization expects CSV files with the following columns:
- `target_model`: Name of the language model
- `test_case`: Type of jailbreak test case
- `jailbreak_tactic`: Tactic used for the attempt
- `turn_type`: Either 'multi' or 'single'
- `scores`: Array of success scores (0-1)
- `refused`: Number of times the model refused
- `max_round`: Number of rounds in the conversation
- `attacker_model`: Model used to generate attack prompts
- `evaluator_model`: Model used to evaluate success (varies by dataset)

For enhanced_master_data.csv, the visualization provides:
- Scatter plots of ASR vs model size and release date
- Models grouped and colored by company
- Information from model_comparison.csv metadata (size, company, release date)

## Merging Data

The enhanced_master_data.csv file is created by the `enhanced_merge_csv.py` script, which:
- Merges all CSV files in the directory (except excluded files)
- Adds appropriate `attacker_model` and `evaluator_model` columns based on source file
- Preserves the correct evaluator model for each dataset:
  - results_2D.csv: anthropic/claude-3-haiku
  - results_2D_2.csv: openai/gpt-4.1-mini
  - Other files: gpt-4o-mini-2024-07-18

## Development

To modify the visualization:
1. Edit `visualization.jsx` for changes to the charts and layout
2. Update `vite.config.js` for development server configuration
3. Modify `package.json` to add or update dependencies

## Troubleshooting

- If port 3000 is in use, the server will automatically try port 3001
- Check browser console for any error messages
- Ensure CSV files are properly formatted and accessible
- Clear browser cache if changes are not reflecting
- If you get Node.js version errors:
  1. Make sure you've installed nvm correctly
  2. Run `nvm use 18` to switch to the correct version
  3. Try closing and reopening your terminal 