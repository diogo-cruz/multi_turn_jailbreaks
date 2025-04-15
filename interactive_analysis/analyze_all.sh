#!/bin/bash

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