#!/bin/bash

# =============================================================================
# Free Model Jailbreak Testing with Rate Limiting (Fixed Version)
# =============================================================================
#
# This script is specialized for running jailbreak attack tests against free-tier
# language models that often have strict rate limits. It includes enhanced error
# handling and rate limit management with exponential backoff to ensure tests can
# complete successfully despite API restrictions.
#
# Key features:
# - Optimized for free API models from providers like OpenRouter
# - Handles rate limiting with exponential backoff retry mechanism
# - Skips combinations that already have results to avoid redundant API calls
# - Sanitizes filenames for proper log storage
# - Configurable parallel execution with careful throttling
# - Support for a wide variety of free models including:
#   * Google Gemma models (various sizes)
#   * Nvidia Nemotron models
#   * Meta Llama models
#   * DeepSeek models
#   * Mistral models
#
# This script is particularly useful when you want to evaluate jailbreak 
# effectiveness across many models without incurring API costs.
#
# Requirements:
# - GNU Parallel must be installed
# - OpenRouter API key configured in .env file
# - Python environment with required dependencies
#
# Usage:
#   ./run_attacks_parallel_free_ratelimit_fixed.sh
#
# =============================================================================

# Number of parallel processes to run (reduced to prevent too many concurrent requests)
THREAD_COUNT=8

# Load the API key from .env file
if [ -f .env ]; then
    source .env
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "Error: OPENROUTER_API_KEY not found in .env file."
        exit 1
    fi
    # Export the API key so it can be used by Python
    export OPENAI_API_KEY="$OPENROUTER_API_KEY"
else
    echo "Error: .env file not found. Please create it with your OPENROUTER_API_KEY."
    exit 1
fi

# Define the values for each parameter - using only those from the original script
jailbreak_tactics=(
    "crescendomation" 
    "actor_attack" 
    "opposite_day" 
    "direct_request"
    "emotional_appeal"
    "command"
    "crowding"
)

# Test cases from original script
test_cases=(
    "non_violent_crimes_2_alt1"
    "non_violent_crimes_2_alt2"
    "non_violent_crimes_4_alt1"
    "sexual_content_1_alt1"
    "sexual_content_3_alt1"
    "sexual_content_4_alt1"
    "sexual_content_4_alt2"
)

# Target models - all free models as listed by the user
target_models=(
    # Original requested Gemma models
    "google/gemma-3-1b-it:free"
    "google/gemma-3-4b-it:free"
    "google/gemma-3-12b-it:free"
    "google/gemma-3-27b-it:free"
    
    # Additional Nvidia models
    "nvidia/llama-3.1-nemotron-nano-8b-v1:free"
    "nvidia/llama-3.3-nemotron-super-49b-v1:free"
    "nvidia/llama-3.1-nemotron-ultra-253b-v1:free"
    
    # Meta models
    "meta-llama/llama-4-maverick:free"
    "meta-llama/llama-4-scout:free"
    
    # Deepseek models
    "deepseek/deepseek-v3-base:free"
    "deepseek/deepseek-chat-v3-0324:free"
    
    # Mistral models
    "mistralai/mistral-small-3.1-24b-instruct:free"
    "mistralai/mixtral-8x7b-instruct:free"
)

# Fixed temperature
temperatures=(
    "0.0"
)

# Both turn types
turn_types=(
    "single_turn"
    "multi_turn"
)

# Use a powerful free model for the attacker
attacker_models=(
    "mistralai/mixtral-8x7b-instruct:free"
)

# Static values
target_base_url="https://openrouter.ai/api/v1"
attacker_base_url="https://openrouter.ai/api/v1"

# Create results directory if it doesn't exist
RESULTS_DIR="clean_results/strongreject_results"
mkdir -p "$RESULTS_DIR"

# Create a log directory for parallel job outputs
LOG_DIR="parallel_logs"
mkdir -p "$LOG_DIR"

# Function to count total combinations
count_total_combinations() {
    local count=0
    for tactic in "${jailbreak_tactics[@]}"; do
        for test_case in "${test_cases[@]}"; do
            for target_model in "${target_models[@]}"; do
                for temp in "${temperatures[@]}"; do
                    for turn_type in "${turn_types[@]}"; do
                        for attacker_model in "${attacker_models[@]}"; do
                            # Skip if jailbreak tactic doesn't have single turn and turn_type is single_turn
                            if [[ "$turn_type" == "single_turn" ]]; then
                                # Check if the tactic has a single turn implementation
                                if ! grep -q "def single_turn" "jailbreaks/$tactic/run.py" 2>/dev/null; then
                                    continue
                                fi
                            fi
                            ((count++))
                        done
                    done
                done
            done
        done
    done
    echo $count
}

# Function to check if result already exists
result_exists() {
    local tactic=$1
    local test_case=$2
    local target_model=$3
    local turn_type=$4
    
    # Check if directory exists
    if [ ! -d "$RESULTS_DIR/$tactic" ]; then
        return 1  # Result doesn't exist
    fi
    
    # Extract the base model name without provider prefix and :free suffix
    model_name=$(echo "$target_model" | awk -F/ '{print $NF}' | sed 's/:free//')
    
    # First check: Look for exact filename match in the directory
    if find "$RESULTS_DIR/$tactic" -name "${tactic}_${test_case}_${model_name}_${turn_type}_*.jsonl" 2>/dev/null | grep -q .; then
        echo "Found exact match: ${tactic}_${test_case}_${model_name}_${turn_type}" >&2
        return 0  # Result exists
    fi
    
    # Second check: More flexible match for model names with special characters
    # Extract a simpler model pattern (e.g., gemma-3-1b-it, nemotron-nano, etc.)
    local model_pattern=""
    if [[ "$target_model" == *"gemma-3-1b-it"* ]]; then
        model_pattern="gemma-3-1b-it"
    elif [[ "$target_model" == *"gemma-3-4b-it"* ]]; then
        model_pattern="gemma-3-4b-it"
    elif [[ "$target_model" == *"gemma-3-12b-it"* ]]; then
        model_pattern="gemma-3-12b-it"
    elif [[ "$target_model" == *"gemma-3-27b-it"* ]]; then
        model_pattern="gemma-3-27b-it"
    elif [[ "$target_model" == *"nemotron-nano"* ]]; then
        model_pattern="nemotron-nano"
    elif [[ "$target_model" == *"nemotron-super"* ]]; then
        model_pattern="nemotron-super"
    elif [[ "$target_model" == *"nemotron-ultra"* ]]; then
        model_pattern="nemotron-ultra"
    elif [[ "$target_model" == *"llama-4-maverick"* ]]; then
        model_pattern="llama-4-maverick"
    elif [[ "$target_model" == *"llama-4-scout"* ]]; then
        model_pattern="llama-4-scout"
    elif [[ "$target_model" == *"deepseek-v3-base"* ]]; then
        model_pattern="deepseek-v3-base"
    elif [[ "$target_model" == *"deepseek-chat-v3"* ]]; then
        model_pattern="deepseek-chat-v3"
    elif [[ "$target_model" == *"mistral-small"* ]]; then
        model_pattern="mistral-small"
    elif [[ "$target_model" == *"mixtral-8x7b"* ]]; then
        model_pattern="mixtral-8x7b"
    else
        model_pattern=$(echo "$model_name" | cut -d'-' -f1)
    fi
    
    if find "$RESULTS_DIR/$tactic" -name "${tactic}_${test_case}_*${model_pattern}*_${turn_type}_*.jsonl" 2>/dev/null | grep -q .; then
        echo "Found pattern match: ${tactic}_${test_case}_*${model_pattern}*_${turn_type}" >&2
        return 0  # Result exists
    fi
    
    return 1  # Result doesn't exist
}

# Function to sanitize filename
sanitize_filename() {
    echo "$1" | sed 's/\//_/g' | sed 's/:/_/g'
}

# Function to generate commands
generate_commands() {
    local job_id=0
    local skipped=0
    
    for tactic in "${jailbreak_tactics[@]}"; do
        for test_case in "${test_cases[@]}"; do
            for target_model in "${target_models[@]}"; do
                for temp in "${temperatures[@]}"; do
                    for turn_type in "${turn_types[@]}"; do
                        for attacker_model in "${attacker_models[@]}"; do
                            # Skip if jailbreak tactic doesn't have single turn and turn_type is single_turn
                            if [[ "$turn_type" == "single_turn" ]]; then
                                # Check if the tactic has a single turn implementation
                                if ! grep -q "def single_turn" "jailbreaks/$tactic/run.py" 2>/dev/null; then
                                    continue
                                fi
                            fi
                            
                            # Check if result already exists
                            if result_exists "$tactic" "$test_case" "$target_model" "$turn_type"; then
                                ((skipped++))
                                continue  # Skip this combination
                            fi
                            
                            ((job_id++))
                            
                            # Sanitize model names for log filename
                            sanitized_target_model=$(sanitize_filename "$target_model")
                            
                            # Use the fixed rate-limited version of the main script
                            # Add timeout and log output to job-specific file
                            echo "{ echo Starting job $job_id: $tactic - $test_case - $target_model - $turn_type; \
                                   timeout 3600 python main_ratelimit.py \
                                   --jailbreak-tactic \"$tactic\" \
                                   --test-case \"$test_case\" \
                                   --target-model \"$target_model\" \
                                   --attacker-model \"$attacker_model\" \
                                   --target-base-url \"$target_base_url\" \
                                   --attacker-base-url \"$attacker_base_url\" \
                                   --target-temp $temp \
                                   --attacker-temp $temp \
                                   --turn-type \"$turn_type\"; \
                                   echo Finished job $job_id with status \$?; } 2>&1 | tee \"$LOG_DIR/job_${job_id}_${tactic}_${test_case}_${sanitized_target_model}_${turn_type}.log\""
                        done
                    done
                done
            done
        done
    done
    
    echo "Skipped $skipped combinations that already have results" >&2
}

# Check if parallel is installed
if ! command -v parallel &> /dev/null; then
    echo "GNU Parallel is not installed. Please install it first:"
    echo "On macOS: brew install parallel"
    echo "On Ubuntu/Debian: sudo apt-get install parallel"
    exit 1
fi

# Count total combinations
TOTAL_COMBINATIONS=$(count_total_combinations)
echo "Total number of combinations to run: $TOTAL_COMBINATIONS"
echo "Running with $THREAD_COUNT parallel processes..."
echo "Using OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:5}...${OPENROUTER_API_KEY: -5}"
echo "Using fixed rate-limited script with automatic retry mechanism and NoneType fix"
echo "Job logs will be saved to $LOG_DIR directory"
echo "Will skip combinations that already have results"

# Run with progress tracking and more staggered starts
# --delay of 5 seconds between job starts to reduce initial burst of requests
# --timeout 3600 to time out any jobs that run for more than 1 hour
# --joblog to track job status and retry failed jobs if needed
generate_commands | parallel --delay 5 --timeout 3600 --joblog "$LOG_DIR/parallel_joblog.txt" \
                             -j "$THREAD_COUNT" --bar --colsep ' ' {} 