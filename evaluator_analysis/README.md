# Evaluator Analysis

This is an interactive visualization tool for analyzing the master_results.csv dataset of evaluator results.

## Features

- Interactive visualization of evaluator results
- Filter and analyze data by model, test case, and prompt
- View success rates across different dimensions
- Compare performance across models and test cases
- Detailed prompt analysis with result tables

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

You can filter the data using the dropdown selectors at the top of the page.

## Data Structure

The tool expects the master_results.csv file to contain at least the following columns:

- `model`: The model being evaluated
- `test_case`: The test case being evaluated
- `prompt_path`: The path to the prompt file
- `success`: A boolean or numeric (0/1) indicating whether the test was successful
- `response`: The model response (optional) 