# Evaluator Analysis

This is an interactive visualization tool for analyzing the master_results.csv dataset of evaluator results, similar to the interactive_analysis tool but focused specifically on evaluator data.

## Features

- Interactive visualization of evaluator results
- Multiple chart types (bar charts, line charts, pie charts, scatter plots, radar charts)
- Filter and analyze data by model, test case, and prompt
- Sort data by different metrics (success rate, sample count, alphabetically)
- View success rates across different dimensions
- Compare performance across models and test cases
- Detailed prompt analysis with result tables
- Standard error calculations for statistical significance
- Detailed view option for in-depth analysis

## Setup

1. Make sure you have Node.js and npm installed
2. Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

3. Start the development server:

```bash
npm start
```

4. Open your browser and navigate to http://localhost:5173

## Usage

The interface is divided into several tabs:

- **Overview**: Shows a summary of the dataset and top-performing models and test cases
- **Models**: Allows detailed analysis of model performance across test cases
- **Test Cases**: Shows performance of different test cases and how models perform on each
- **Prompts**: Provides detailed analysis of prompts within a selected test case

### Chart Types

You can toggle between different chart types:

- Bar Chart: Best for comparing values across categories
- Line Chart: Good for showing trends
- Scatter Plot: Useful for showing relationships between two variables
- Pie Chart: Shows proportions of a whole
- Radar Chart: Compares multiple variables
- Composed Chart: Combines multiple chart types for complex visualizations

### Filtering and Sorting

You can filter the data using the dropdown selectors at the top of the page:

- Filter by model
- Filter by test case
- Filter by prompt (when in prompts tab)
- Sort by success rate, failure rate, total count, or name

### Detail View

Toggle the "Show Details" checkbox to see:

- Standard error bars on charts
- Detailed data tables
- Additional statistics

## Data Structure

The tool expects the master_results.csv file to contain at least the following columns:

- `model`: The model being evaluated
- `test_case`: The test case being evaluated
- `prompt_path`: The path to the prompt file
- `success`: A boolean or numeric (0/1) indicating whether the test was successful
- `response`: The model response (optional) 