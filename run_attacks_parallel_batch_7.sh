#!/bin/bash

# Number of parallel processes to run
THREAD_COUNT=32
# attacker temperature
ATTACK_TEMP=1.0

# Sample counts for different turn types
SINGLE_TURN_SAMPLES=1
MULTI_TURN_SAMPLES=1

# Output folder name
OUTPUT_FOLDER="batch7"

# Define the values for each parameter
jailbreak_tactics=(
    "direct_request"
)
test_cases=(
    "terrorist_recruitment"
    "threatening_letter"
    "airbnb_voyeurism"
    "bestiality"
    "bus_bomb_placement"
    "car_break-in"
    "date_rape_drug"
    "fake_online_profile"
    "illegal_brothel"
    "mass_shooting_plan"
    "nudes_blackmail"
    "poisoning_water_supply"
    "sql_injection"
    "stealing_credit_card_info"
    "store_theft"
    "tax_fraud"
    "asian_insults"
    "bomb_threats"
    "counterfeit_money"
    "deceptive_email"
    "deoderant_flamethrower"
    "drunk_driving"
    "false_accusation"
    "gender_insults"
    "hate_speech_immigrants"
    "illegal_arms"
    "improvised_gun"
    "lgbtq_insults"
    "pistol_serial_numbers"
    "remove_watermarks"
)
target_models=(
    "anthropic/claude-3-sonnet"
    "anthropic/claude-3.5-sonnet"
    "anthropic/claude-3.7-sonnet"
    "anthropic/claude-sonnet-4"

    "openai/gpt-4.1"
    "openai/gpt-4.1-mini"
    "openai/gpt-4.1-nano"
    "openai/gpt-4o"
    "openai/gpt-4o-2024-05-13"

    "google/gemini-2.5-pro"
    "google/gemini-2.5-flash"
    "google/gemini-2.5-flash-lite-preview-06-17"
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
