#!/bin/bash

# Set up the evaluator analysis project
set -e  # exit immediately if a command exits with a non-zero status

echo "==== Evaluator Analysis Setup ===="

# Install dependencies
echo "Installing dependencies..."
npm install

# Create public directory if it doesn't exist
echo "Setting up directories..."
mkdir -p public

# Copy the master_results.csv file if not already there
if [ ! -f public/master_results.csv ]; then
  echo "Copying master_results.csv to public directory..."
  if [ -f ../csv_results/master_results.csv ]; then
    cp ../csv_results/master_results.csv public/
    echo "CSV file copied successfully."
  else
    echo "Error: master_results.csv not found in csv_results directory!"
    echo "Please manually copy the CSV file to evaluator_analysis/public/ directory."
    exit 1
  fi
else
  echo "CSV file already exists in public directory."
fi

echo ""
echo "Setup complete! Run 'npm start' to start the application."
echo "Then open your browser and navigate to http://localhost:5173"
echo "" 