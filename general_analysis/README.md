# Jailbreak Analysis Visualization Tool

This tool provides a unified interface for analyzing jailbreak attacks against various language models. It combines components from both the `interactive_analysis` and `evaluator_analysis` projects.

## Features

-   Unified data loading from multiple sources.
-   Interactive filtering by model, test case, tactic, and evaluator.
-   Visualization of results using charts and tables.
-   Side-by-side comparison of different attack configurations.
-   Debug mode for inspecting raw data and intermediate calculations.

## Data Sources

The tool uses the following CSV files located in `public/data/`:

-   `results.csv`: Main results file
-   `batch_2C_results.csv`: Batch 2C results
-   `batch_2D_results.csv`: Batch 2D results
-   `batch_3A_results.csv`: Batch 3A results
-   `batch_4A_results.csv`: Batch 4A results
-   `batch_4B_results.csv`: Batch 4B results
-   `batch_4B_fixed_20250501_results.csv`: Batch 4B fixed results
-   `results_final_3samples.csv`: Final 3-sample results

## Getting Started

1.  Run the setup script to copy required data and install dependencies:
    ```bash
    ./setup.sh
    ```

    This script:

    -   Installs NPM dependencies
    -   Creates necessary directories
    -   Copies data files from interactive_analysis and evaluator_analysis directories
    -   Sets up configuration files for Vite, PostCSS, and Tailwind CSS

2.  Start the development server:
    ```bash
    npm run dev
    ```

3.  Open the provided URL in your browser (typically http://localhost:5173)

## Implementation Details

-   Built with React 18 and Vite 4
-   Uses Recharts for data visualization
-   Uses TailwindCSS for styling
-   Uses Papa Parse for CSV parsing
-   Implements D3 scale and color functions for advanced visualizations
-   Supports dynamic file selection and filtering by model, test case, tactic, and evaluator
-   Implements responsive layouts that work on various screen sizes

## Additional Tools

-   `calc_asr.py`: Python script for calculating Attack Success Rate (ASR).
-   `check_asr_calculation.py`: Python script for verifying ASR calculations.
-   `test_asr_calculation.js`: JavaScript tests for ASR calculations.
-   `check_csv_format.py`: Python script for validating CSV file formats.

# General Analysis Visualization (New Instructions)

This section provides instructions for setting up and running the visualization if you are starting with just this `general_analysis` folder.

## Setup

1.  **Navigate to the `general_analysis` directory:**
    ```bash
    cd general_analysis
    ```
2.  **Install dependencies:**
    Make sure you have Node.js and npm installed. Then, run the following command to install the project dependencies:
    ```bash
    npm install
    ```
    *Note: The existing `setup.sh` script also performs `npm install` along with other project-specific setup steps. If you are setting up the broader project, prefer using `./setup.sh` as described in the "Getting Started" section above.* 

## Running the Visualization

1.  **Start the development server:**
    ```bash
    npm run dev
    ```
2.  **Open in browser:**
    This will typically start a local development server (often on `http://localhost:5173` or a similar port shown in your terminal). Open the provided URL in your web browser to view the visualization.

## Project Structure (Relevant to this visualization)

-   `src/`: Contains the source code for the visualization.
-   `public/`: Contains static assets, including data files (which might need to be populated by `setup.sh` for full functionality).
-   `package.json`: Defines the project dependencies and scripts.
-   `vite.config.js`: Configuration file for Vite.
-   `tailwind.config.js`: Configuration file for Tailwind CSS.

## Features

The visualization tool includes:

- **Model Performance Analysis**: Compare success rates, refusal rates, and interaction rounds across different models.
- **Test Case Analysis**: Analyze performance across different test cases and compare how models respond to each.
- **Tactic Effectiveness**: Evaluate which jailbreak tactics are most effective and how they perform against different models.
- **Evaluator Analysis**: Compare various evaluator models and how they judge jailbreak attempts.
- **Evaluator Correlation Analysis**: Measure agreement between different evaluator models when judging the same examples.
- **Reasoning Analysis**: Analyze how different levels of reasoning effort affect attack success rates.
- **Model Comparison Heatmap**: Visualize comparative performance across models, tactics, and test cases.
- **Size Analysis**: Explore the relationship between model size (parameters) and jailbreak resistance.
- **Release Analysis**: Analyze performance trends across different model releases and versions.

## Directory Structure

### Root Directory
- **README.md**: This documentation file
- **setup.sh**: Setup script that initializes the environment, copies data, and configures dependencies
- **package.json**: Node.js package configuration with dependencies and scripts
- **index.html**: Main HTML entry point for the web application
- **vite.config.js**: Configuration for the Vite build tool
- **postcss.config.js**: PostCSS configuration for CSS processing
- **tailwind.config.js**: Tailwind CSS framework configuration

### `/src` Directory
Contains the React application source code.
- **App.jsx**: Main React application component
- **main.jsx**: Entry point for the React application
- **index.css**: Global CSS styles
- **CombinedVisualization.jsx**: Core component that integrates all visualizations

#### `/src/components` Directory
Contains individual visualization components:
- **ModelPerformance.jsx**: For comparing overall model performance metrics
- **TestCaseAnalysis.jsx**: For analyzing test case performance across models
- **TacticEffectiveness.jsx**: For comparing jailbreak tactic effectiveness
- **EvaluatorAnalysis.jsx**: For analyzing evaluator model performance
- **EvaluatorCorrelationAnalysis.jsx**: For evaluator correlation analysis
- **ReasoningAnalysis.jsx**: For analyzing reasoning effort impact on success rates
- **ModelComparisonHeatmap.jsx**: For heatmap visualizations of model performance
- **SizeAnalysis.jsx**: For analyzing relationship between model size and performance
- **ReleaseAnalysis.jsx**: For analyzing model performance across release timeline

#### `/src/utils` Directory
Contains utility functions for data processing:
- **dataProcessing.js**: Core utilities for processing and transforming jailbreak data
- **dataProcessing.js.bak**: Backup of the data processing utilities

### `/public` Directory
Contains static assets and data files served directly to clients.

#### `/public/data` Directory
Contains CSV datasets used by the visualization:
- **master_results.csv**: Primary dataset with jailbreak attempt results
- **enhanced_master_data.csv**: Enhanced data with additional metadata
- **model_comparison.csv**: Model parameter and size information
- **results_test_runs.csv**: Test run data
- **batch_4B_fixed_20250501_results.csv**: Batch 4B fixed results
- **batch_4A_results.csv**: Batch 4A results
- **batch_4B_results.csv**: Batch 4B results
- **sample_results.csv**: Sample data for testing

### `/dist` Directory
Contains the built application for production deployment:
- **/assets**: Compiled and minified JavaScript, CSS, and other assets
- **index.html**: Production HTML entry point
- **/data**: Copied data files for the production build

### `/figures` Directory
Contains visualization outputs as PNG and PDF files, including:
- Model performance charts
- Test case analysis visualizations
- Tactic effectiveness visualizations
- Heatmaps and scatter plots
- Results from various experimental batches (test_runs, final_3samples, etc.)

### Utility Scripts
Python and JavaScript utilities for data analysis:
- **calc_asr.py**: Calculate Attack Success Rate (ASR) metrics
- **check_asr_calculation.py**: Verify ASR calculation accuracy
- **test_asr_calculation.js**: JavaScript tests for ASR calculations
- **check_csv_format.py**: Validate the format of CSV data files

## Data Sources

The tool can load data from multiple CSV files:
- `master_results.csv`: Primary dataset with jailbreak attempt results
- `enhanced_master_data.csv`: Enhanced data with additional metadata
- `model_comparison.csv`: Model parameter and size information
- `results_test_runs.csv`: Test run data
- `batch_4B_fixed_20250501_results.csv`: Batch 4B fixed results
- `results_final_3samples.csv`: Final 3-sample results

## Additional Tools

The general_analysis directory also includes several Python and JavaScript utilities:
- `calc_asr.py`: Calculate Attack Success Rate (ASR) metrics
- `check_asr_calculation.py`: Verify ASR calculation accuracy
- `test_asr_calculation.js`: JavaScript tests for ASR calculations
- `check_csv_format.py`: Validate the format of CSV data files 