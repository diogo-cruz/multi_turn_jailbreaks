#!/bin/bash

# Number of parallel processes to run
THREAD_COUNT=128
# attacker temperature
ATTACK_TEMP=1.0

# If you need multiple samples of the same combination, set that here
SAMPLES=1

# Output folder name
OUTPUT_FOLDER="batch_4E_test"

# Define the values for each parameter
jailbreak_tactics=(
    "direct_request"
)
test_cases=(
    "remove_watermarks"
)
target_models=(
    "qwen/qwen3-0.6b-04-28:free"
)
temperatures=(
    "0.0"
)
turn_types=(
    "multi_turn"
)

attacker_models=(
    "openai/gpt-4o-mini"
)

reasoning=(
    "high"
)

# Static values
target_base_url="https://openrouter.ai/api/v1"
attacker_base_url="https://openrouter.ai/api/v1"

# Evaluator
evaluator_model="openai/gpt-4o-mini"
evaluator_temp="0.0"

# Function to count total combinations
count_total_combinations() {
    local count=0
    for tactic in "${jailbreak_tactics[@]}"; do
        for test_case in "${test_cases[@]}"; do
            for target_model in "${target_models[@]}"; do
                for temp in "${temperatures[@]}"; do
                    for turn_type in "${turn_types[@]}"; do
                        for attacker_model in "${attacker_models[@]}"; do
                            for reasoning in "${reasoning[@]}"; do
                                ((count++))
                            done
                        done
                    done
                done
            done
        done
    done
    echo $count
}

# Function to generate commands
generate_commands() {
    for tactic in "${jailbreak_tactics[@]}"; do
        for test_case in "${test_cases[@]}"; do
            for target_model in "${target_models[@]}"; do
                for temp in "${temperatures[@]}"; do
                    for turn_type in "${turn_types[@]}"; do
                        for attacker_model in "${attacker_models[@]}"; do
                            for reasoning in "${reasoning[@]}"; do
                                echo "python main.py \
                                    --jailbreak-tactic \"$tactic\" \
                                    --test-case \"$test_case\" \
                                    --target-model \"$target_model\" \
                                    --attacker-model \"$attacker_model\" \
                                    --target-base-url \"$target_base_url\" \
                                    --attacker-base-url \"$attacker_base_url\" \
                                    --target-temp $temp \
                                    --attacker-temp $ATTACK_TEMP \
                                    --turn-type \"$turn_type\" \
                                    --reasoning \"$reasoning\" \
                                    --samples $SAMPLES \
                                    --evaluator-model \"$evaluator_model\" \
                                    --evaluator-temp $evaluator_temp \
                                    --output-folder \"$OUTPUT_FOLDER\""
                            done
                        done
                    done
                done
            done
        done
    done
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

# Run with progress tracking
generate_commands | parallel -j "$THREAD_COUNT" --bar --colsep ' ' {} 