#!/bin/bash

# =============================================================================
# Parallel Jailbreak Attack Reevaluation Runner
# =============================================================================
#
# This script enables parallel reevaluation of existing jailbreak attack results
# using alternative evaluation criteria or models. It allows researchers to apply
# new evaluation methodologies to previously collected attack data without 
# rerunning the actual attacks.
#
# Key features:
# - Parallel processing of reevaluation tasks using GNU Parallel
# - Support for different evaluator models and evaluation techniques
# - Intelligent file discovery across multiple result directories
# - Preservation of original attack data with new evaluation metrics
# - Detailed logging of reevaluation progress
#
# This script is particularly useful when:
# - New evaluation metrics are developed that need to be applied to existing data
# - Comparing different evaluator models' assessments of the same attack results
# - Validating evaluation consistency across different methodologies
#
# Usage:
#   ./run_reevaluation_parallel.sh [evaluator_model]
#
# Parameters:
#   evaluator_model - Optional model to use for reevaluation
#
# =============================================================================

# Activate the conda environment
# This line ensures we have the right environment for the project
source ~/anaconda3/etc/profile.d/conda.sh
conda activate multi_turn_jailbreaks

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --results-folder)
            RESULTS_FOLDER="$2"
            shift
            ;;
        --evaluator-models)
            # Allow comma-separated list of models
            IFS=',' read -r -a EVALUATOR_MODELS <<< "$2"
            shift
            ;;
        --evaluator-base-url)
            EVALUATOR_BASE_URL="$2"
            shift
            ;;
        --evaluator-temp)
            EVALUATOR_TEMP="$2"
            shift
            ;;
        --max-workers)
            MAX_WORKERS="$2"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            ;;
        --verbose)
            VERBOSE="--verbose"
            ;;
        --debug)
            DEBUG="--debug"
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Check for required parameters
if [ -z "$RESULTS_FOLDER" ]; then
    echo "Error: --results-folder is required"
    exit 1
fi

if [ -z "$EVALUATOR_MODELS" ]; then
    echo "Error: --evaluator-models is required (comma-separated list)"
    echo "Example: --evaluator-models 'openai/gpt-4o,anthropic/claude-3.5-sonnet'"
    exit 1
fi

# Set defaults for optional parameters
EVALUATOR_BASE_URL=${EVALUATOR_BASE_URL:-"https://openrouter.ai/api/v1"}
EVALUATOR_TEMP=${EVALUATOR_TEMP:-"0.0"}
MAX_WORKERS=${MAX_WORKERS:-16}
DRY_RUN=${DRY_RUN:-""}
VERBOSE=${VERBOSE:-""}
DEBUG=${DEBUG:-""}

echo "Running reevaluation with the following parameters:"
echo "Results folder: $RESULTS_FOLDER"
echo "Evaluator models: ${EVALUATOR_MODELS[*]}"
echo "Evaluator base URL: $EVALUATOR_BASE_URL"
echo "Evaluator temperature: $EVALUATOR_TEMP"
echo "Max workers: $MAX_WORKERS"
echo "API Key: [Using from .env file]"
if [[ -n "$DRY_RUN" ]]; then
    echo "Dry run: Yes (no files will be modified)"
fi
if [[ -n "$VERBOSE" ]]; then
    echo "Verbose output: Yes"
fi
if [[ -n "$DEBUG" ]]; then
    echo "Debug mode: Yes (sequential processing with detailed output)"
fi

# Run for each evaluator model
for EVALUATOR_MODEL in "${EVALUATOR_MODELS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Starting evaluation with model: $EVALUATOR_MODEL"
    echo "--------------------------------------------------------------------------------"
    
    # Run the Python script
    python reevaluate_responses.py \
        --results-folder "$RESULTS_FOLDER" \
        --evaluator-model "$EVALUATOR_MODEL" \
        --evaluator-base-url "$EVALUATOR_BASE_URL" \
        --evaluator-temp "$EVALUATOR_TEMP" \
        --max-workers "$MAX_WORKERS" \
        $DRY_RUN $VERBOSE $DEBUG
    
    echo "--------------------------------------------------------------------------------"
    echo "Completed evaluation with model: $EVALUATOR_MODEL"
    echo "--------------------------------------------------------------------------------"
done

echo "All reevaluations complete!" 