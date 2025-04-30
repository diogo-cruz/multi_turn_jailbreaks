#!/bin/bash

# =============================================================================
# Parallel Robust Jailbreak Evaluation Runner
# =============================================================================
#
# This script provides a parallelized version of the robust evaluation framework,
# enabling high-throughput evaluation of multiple jailbreak attack results 
# simultaneously. It leverages GNU Parallel to distribute the evaluation workload
# across multiple CPU cores, significantly speeding up the evaluation process for
# large datasets of attack results.
#
# Key features:
# - Parallel processing of evaluation tasks using GNU Parallel
# - Configurable number of worker processes
# - Comprehensive file discovery across multiple directories
# - Detailed logging of evaluation progress
# - Support for multiple evaluator models
#
# This script is particularly valuable when evaluating large-scale attack campaigns
# that might include thousands of individual result files. The parallel execution
# dramatically reduces total evaluation time compared to the sequential version.
#
# Usage:
#   ./run_robust_evaluation_parallel.sh [evaluator_model]
#
# Parameters:
#   evaluator_model - Optional model name for evaluation (default: claude-3-haiku-20240307)
#
# See README_robust_evaluation.md for more details on the evaluation methodology.
#
# =============================================================================

# Activate the conda environment if available
if [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
    conda activate multi_turn_jailbreaks 2>/dev/null || true
fi

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --results-folder|--input-path)
            INPUT_PATH="$2"
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
        --log-file)
            LOG_FILE="$2"
            shift
            ;;
        --force)
            FORCE="--force"
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
if [ -z "$INPUT_PATH" ]; then
    echo "Error: --results-folder or --input-path is required"
    exit 1
fi

# Check if input path exists
if [ ! -e "$INPUT_PATH" ]; then
    echo "Error: Input path '$INPUT_PATH' does not exist"
    exit 1
fi

if [ -z "$EVALUATOR_MODELS" ]; then
    # Default to a single model if not specified
    EVALUATOR_MODELS=("openai/gpt-4.1-nano")
    echo "No evaluator models specified, using default: ${EVALUATOR_MODELS[0]}"
fi

# Set defaults for optional parameters
EVALUATOR_BASE_URL=${EVALUATOR_BASE_URL:-"https://openrouter.ai/api/v1"}
EVALUATOR_TEMP=${EVALUATOR_TEMP:-"0.0"}
MAX_WORKERS=${MAX_WORKERS:-16}
FORCE=${FORCE:-""}
VERBOSE=${VERBOSE:-""}
DEBUG=${DEBUG:-""}
LOG_FILE_PARAM=""
if [ -n "$LOG_FILE" ]; then
    LOG_FILE_PARAM="--log-file $LOG_FILE"
fi

# Determine if input is a file or directory
if [ -f "$INPUT_PATH" ]; then
    INPUT_TYPE="file"
    echo "Input is a single file: $INPUT_PATH"
else
    INPUT_TYPE="directory"
    echo "Input is a directory: $INPUT_PATH"
fi

echo "Running robust evaluation in parallel with the following parameters:"
echo "Input path: $INPUT_PATH"
echo "Evaluator models: ${EVALUATOR_MODELS[*]}"
echo "Evaluator base URL: $EVALUATOR_BASE_URL"
echo "Evaluator temperature: $EVALUATOR_TEMP"
echo "Max workers: $MAX_WORKERS"
echo "API Key: [Using from .env file]"
if [[ -n "$LOG_FILE" ]]; then
    echo "Custom log file: $LOG_FILE"
else
    echo "Log file: [Auto-generated in evaluation_logs directory]"
fi
if [[ -n "$FORCE" ]]; then
    echo "Force overwrite: Yes"
fi
if [[ -n "$VERBOSE" ]]; then
    echo "Verbose output: Yes"
fi
if [[ -n "$DEBUG" ]]; then
    echo "Debug mode: Yes (sequential processing with detailed output)"
fi

# Create a log directory if it doesn't exist
LOG_DIR="parallel_logs"
mkdir -p "$LOG_DIR"

# Run for each evaluator model
for EVALUATOR_MODEL in "${EVALUATOR_MODELS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Starting robust evaluation with model: $EVALUATOR_MODEL"
    echo "--------------------------------------------------------------------------------"
    
    # Create a timestamp for the log file
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    SHELL_LOG_FILE="$LOG_DIR/robust_eval_${EVALUATOR_MODEL//\//_}_${TIMESTAMP}.log"
    
    # Run the Python script with logging
    # Note: In addition to this shell log file, the Python script now logs to evaluation_logs directory
    python robust_evaluation_parallel.py \
        --results-folder "$INPUT_PATH" \
        --evaluator-model "$EVALUATOR_MODEL" \
        --evaluator-base-url "$EVALUATOR_BASE_URL" \
        --evaluator-temp "$EVALUATOR_TEMP" \
        --max-workers "$MAX_WORKERS" \
        $LOG_FILE_PARAM $FORCE $VERBOSE $DEBUG 2>&1 | tee "$SHELL_LOG_FILE"
    
    echo "--------------------------------------------------------------------------------"
    echo "Completed evaluation with model: $EVALUATOR_MODEL"
    echo "Shell output log saved to: $SHELL_LOG_FILE"
    if [[ -z "$LOG_FILE" ]]; then
        echo "Python script log saved to: evaluation_logs/evaluation_*.log"
    else
        echo "Python script log saved to: $LOG_FILE"
    fi
    echo "--------------------------------------------------------------------------------"
done

echo "All robust evaluations complete!" 