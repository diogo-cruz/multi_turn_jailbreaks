#!/bin/bash

# Number of parallel processes to run
THREAD_COUNT=30
# attacker temperature
ATTACK_TEMP=1.0

# Sample counts for different turn types
SINGLE_TURN_SAMPLES=8
MULTI_TURN_SAMPLES=3

# Output folder name
OUTPUT_FOLDER="batch6B"

# Define the values for each parameter
jailbreak_tactics=(
    "direct_request"
    "command"
)
test_cases=(
    "date_rape_drug"
    "airbnb_voyeurism"
    "terrorist_recruitment"
    "remove_watermarks"
    "drunk_driving"
    "false_accusation"
    "lgbtq_insults"
    "counterfeit_money"
    "pistol_serial_numbers"
)
target_models=(
    "anthropic/claude-3.5-sonnet"
)
temperatures=(
    "0.0"
)
turn_types=(
    "single_turn"
    "multi_turn"
)

attacker_models=(
    "openai/gpt-4o-mini"
)

# Static values
model_base_url="https://openrouter.ai/api/v1"

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
                            if [ "$turn_type" = "single_turn" ]; then
                                ((count += SINGLE_TURN_SAMPLES))
                            else
                                ((count += MULTI_TURN_SAMPLES))
                            fi
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
                            # Set samples based on turn type
                            if [ "$turn_type" = "single_turn" ]; then
                                local_samples=$SINGLE_TURN_SAMPLES
                            else
                                local_samples=$MULTI_TURN_SAMPLES
                            fi
                            
                            echo "python main.py \
                                --jailbreak-tactic \"$tactic\" \
                                --test-case \"$test_case\" \
                                --target-model \"$target_model\" \
                                --attacker-model \"$attacker_model\" \
                                --model-base-url \"$model_base_url\" \
                                --target-temp $temp \
                                --attacker-temp $ATTACK_TEMP \
                                --turn-type \"$turn_type\" \
                                --samples $local_samples \
                                --evaluator-model \"$evaluator_model\" \
                                --evaluator-temp $evaluator_temp \
                                --output-folder \"$OUTPUT_FOLDER\""
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
