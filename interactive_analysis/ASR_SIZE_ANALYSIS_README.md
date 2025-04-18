# Model Size vs ASR Analysis for Jailbreak Test Cases

This component provides a detailed analysis of the relationship between model size and Attack Success Rate (ASR) for each test case and AI lab combination in the jailbreak dataset.

## Overview

The analysis focuses on understanding how model size affects vulnerability to different test cases across AI labs. For each test case and AI lab combination, we:

1. Gather all models from that lab
2. Plot the model size (parameters in billions) against the ASR (success rate percentage)
3. Fit a linear regression line to the data points
4. Extract the slope of this line as our key metric

The slope indicates the relationship between model size and jailbreak success:
- **Negative slope**: Larger models tend to be more resistant to the test case
- **Positive slope**: Larger models tend to be more vulnerable to the test case
- **Slope near zero**: No clear relationship between model size and vulnerability

## Running the Analysis

### Prerequisites

- Node.js (v14 or later)
- npm

### Step 1: Install dependencies

```bash
npm install
```

### Step 2: Run the analysis script

```bash
npm run analyze
```

This will:
- Load data from `enhanced_master_data.csv` and `model_comparison.csv`
- Perform linear regression analysis for each test case and lab combination
- Save the results to `size_asr_analysis_results.json`
- Print a summary of findings to the console

### Step 3: Visualize the results in the web interface

```bash
npm start
```

Navigate to the "Size vs ASR Analysis" tab in the interface to view the heatmap visualization.

## Interpreting the Heatmap

The heatmap displays test cases as rows and AI labs as columns. Each cell contains the slope value from the linear regression analysis:

- **Blue cells (negative values)**: As model size increases, jailbreak success rate decreases
- **Red cells (positive values)**: As model size increases, jailbreak success rate increases
- **White/neutral cells**: No clear relationship
- **Gray cells (N/A)**: Insufficient data to calculate (requires at least 2 models with different sizes)

You can sort the heatmap by:
- Test case name (alphabetical)
- Average slope (to see which test cases show the strongest size-related patterns)

## Understanding the Results

This analysis helps answer several important questions:

1. Are larger models generally more resistant to jailbreak attempts?
2. Which test cases show increasing resistance with model size?
3. Which test cases show persistent or increasing vulnerability with model size?
4. Do different AI labs show different patterns in how model size affects security?

The findings can inform AI safety research and help identify which harmful scenarios:
- Are becoming less problematic as models scale up
- Remain persistent challenges regardless of scale
- May actually become more challenging with larger models

## Technical Details

The implementation uses:
- Linear regression to calculate slopes
- React and Recharts for the interactive visualization
- A custom color scale for the heatmap (blue to white to red)

For more details on the calculation methodology, see `test_case_model_size_analysis.js`.

## Limitations

- The analysis requires multiple model sizes from the same lab for each test case
- Small sample sizes may lead to less reliable slope estimates
- The linear relationship assumption may not hold for all test cases
- Model size is just one factor affecting vulnerability (training data, alignment methods, etc. also matter) 