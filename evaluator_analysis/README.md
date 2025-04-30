# Multi-Turn Jailbreaks Analysis Visualization

This project provides an interactive visualization for analyzing multi-turn jailbreak attempts against various language models.

## Overview

The visualization analyzes data from multi-turn jailbreak experiments, displaying success rates and correlations between models, test cases, and tactics.

## Issues Fixed

The visualization component had a temporal dead zone error with the `calculateStandardError` function that was fixed by moving the function declaration before its first use.

## Running the Visualization

```bash
npm run start
```

This will start the development server, and you can access the visualization at http://localhost:5173.

## Visualization Features

- **Data Tables**: View raw data in tabular format
- **Bar Charts**: Visualize success rates by model, tactic, and test case
- **Heatmaps**: View success rate correlation between tactics and test cases
- **Filtering**: Filter data by model, test case, or tactic
- **Sorting**: Sort data by different metrics (success rate, failure rate, etc.)
- **Statistical Analysis**: Includes standard error calculations for confidence intervals

## Data Sources

The visualization can load data from:
- `master_results.csv`: Full dataset (if available)
- `sample_results.csv`: Sample dataset for testing

## Troubleshooting

If the visualization fails to render:

1. Check the browser console for specific error messages
2. Ensure the CSV data files are properly formatted and accessible
3. Verify that all required dependencies are installed 