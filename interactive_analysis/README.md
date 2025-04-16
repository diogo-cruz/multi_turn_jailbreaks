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
└── results_*.csv     # Data files with test results
```

## Features

The visualization includes several interactive views:

1. **Dataset Selection**
   - Choose between different CSV datasets for analysis
   - Currently supports: results_test_runs.csv, results_2D.csv, results_2B.csv, results_final_3samples.csv

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