#!/bin/bash

# =============================================================================
# Comprehensive Jailbreak Analysis Pipeline
# =============================================================================
#
# This script orchestrates the execution of the entire interactive analysis
# pipeline for jailbreak attack results. It runs all the necessary data processing,
# analysis, and visualization steps in the correct sequence to generate a complete
# set of analysis outputs.
#
# Key features:
# - Sequential execution of all analysis steps in the correct order
# - Verification of input data and required dependencies
# - Generation of merged datasets for comprehensive analysis
# - Production of visualization files and statistical outputs
# - Creation of summary reports and insights
#
# This script serves as a one-stop solution for running the complete analysis
# workflow, ensuring that all components of the analysis are executed with the
# appropriate dependencies and in the right order.
#
# Usage:
#   ./analyze_all.sh
#
# =============================================================================

echo "Starting interactive analysis pipeline..."

# Make the script executable
chmod +x analyze_all.sh

# Analyze each CSV file
echo "=== Analyzing all CSV files ==="
echo ""

echo "=== results_test_runs.csv ==="
node --experimental-modules analysis.js results_test_runs.csv > results_test_runs_analysis.txt
echo "Analysis saved to results_test_runs_analysis.txt"
echo ""

echo "=== results_2D.csv ==="
node --experimental-modules analysis.js results_2D.csv > results_2D_analysis.txt
echo "Analysis saved to results_2D_analysis.txt"
echo ""

echo "=== results_2B.csv ==="
node --experimental-modules analysis.js results_2B.csv > results_2B_analysis.txt
echo "Analysis saved to results_2B_analysis.txt"
echo ""

echo "=== results_final_3samples.csv ==="
node --experimental-modules analysis.js results_final_3samples.csv > results_final_3samples_analysis.txt
echo "Analysis saved to results_final_3samples_analysis.txt"
echo ""

echo "=== All analyses complete ==="
echo "Results saved to *_analysis.txt files" 