#!/bin/bash

# =============================================================================
# Robust Jailbreak Evaluation Runner
# =============================================================================
#
# This script automates the process of evaluating jailbreak attack results using
# the robust_evaluation.py framework. It processes JSON result files from completed
# attack runs and produces standardized evaluation metrics for comparing different
# attack methods and model defenses.
#
# The script:
# - Recursively finds all result JSON files in the specified directories
# - Passes each file to the evaluation framework for analysis
# - Organizes evaluation outputs by model, tactic, and test case
# - Provides detailed logging of the evaluation process
#
# This evaluation gives standardized metrics on whether attacks succeeded in
# getting harmful outputs from target models, helping researchers understand
# which jailbreak tactics are most effective against different models.
#
# Usage:
#   ./run_robust_evaluation.sh
#
# See README_robust_evaluation.md for more details on the evaluation methodology.
#
# =============================================================================

# Default evaluator model
EVALUATOR_MODEL="openai/gpt-4.1-nano"

# Function to print usage
usage() {
    echo "Usage: $0 [options] <directory>"
    echo "Options:"
    echo "  -m, --model MODEL   Evaluator model to use (default: openai/gpt-4.1-nano)"
    echo "  -f, --force         Force overwrite of existing files"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -h, --help          Show this help message"
    exit 1
}

# Parse command-line arguments
FORCE=""
VERBOSE=""
DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--model)
            EVALUATOR_MODEL="$2"
            shift 2
            ;;
        -f|--force)
            FORCE="--force"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [[ -z "$DIR" ]]; then
                DIR="$1"
                shift
            else
                echo "Error: Unknown option $1"
                usage
            fi
            ;;
    esac
done

# Check if directory is provided
if [[ -z "$DIR" ]]; then
    echo "Error: Directory is required"
    usage
fi

# Check if directory exists
if [[ ! -d "$DIR" ]]; then
    echo "Error: Directory $DIR does not exist"
    exit 1
fi

# Run the evaluation
echo "Running robust evaluation on $DIR with model $EVALUATOR_MODEL"
echo "Options: Force=$FORCE, Verbose=$VERBOSE"

python robust_evaluation.py "$DIR" --evaluator-model "$EVALUATOR_MODEL" $FORCE $VERBOSE

echo "Evaluation completed!" 