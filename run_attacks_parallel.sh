#!/bin/bash

# Number of parallel processes to run
THREAD_COUNT=8

# Define the values for each parameter
jailbreak_tactics=(
    "crescendomation" 
    # "actor_attack" 
    # "acronym"
    # "opposite_day" 
    "direct_request"
    # "emotional_appeal"
    # "command"
    # "crowding"
    #"allegory"
    #"appeal_to_authority"
)
test_cases=(
    ### StrongREJECT ###
    "deoderant_flamethrower"
    "disarm_police"
    "hate_speech"
    "leak_photos"
    "steal_info"
    "women_drivers"

    ### OLD TEST CASES ###
    # "old/academic_integrity"
    # "old/child_exploitation"
    # "old/corporate_secrets"
    # "old/cybersecurity_exploits"
    # "old/election_interference"
    # "old/extremist_content"
    # "old/figure_out_password"
    # "old/financial_fraud"
    # "old/how_to_make_meth" 
    # "old/how_to_make_bomb"
    # "old/human_trafficking"
    # "old/identity_theft"
    # "old/medical_privacy"
    # "old/racial_slurs"
    # "old/misinformation_annexation_of_crimea_russia"
)
target_models=(
    # "meta-llama/llama-3.1-8b-instruct"
    # "meta-llama/llama-3.1-70b-instruct"
    # "meta-llama/llama-3.1-405b-instruct"
    # "meta-llama/llama-3.2-1b-instruct"
    # "meta-llama/llama-3.2-3b-instruct"
    # "meta-llama/llama-3.3-70b-instruct"
    "gpt-4o-mini-2024-07-18"
)
temperatures=(
    "0.0"
    # "1.0"
)
turn_types=(
    # "single_turn"
    "multi_turn"
)

attacker_models=(
    "gpt-4o-mini-2024-07-18"
    # "cognitivecomputations/dolphin-mixtral-8x7b"
    #"cohere/command-r-plus"
    #"nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
)

# Static values
target_base_url="https://openrouter.ai/api/v1"
attacker_base_url="https://openrouter.ai/api/v1"

# Function to count total combinations
count_total_combinations() {
    local count=0
    for tactic in "${jailbreak_tactics[@]}"; do
        for test_case in "${test_cases[@]}"; do
            for target_model in "${target_models[@]}"; do
                for temp in "${temperatures[@]}"; do
                    for turn_type in "${turn_types[@]}"; do
                        for attacker_model in "${attacker_models[@]}"; do
                            ((count++))
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
                            echo "python main.py \
                                --jailbreak-tactic \"$tactic\" \
                                --test-case \"$test_case\" \
                                --target-model \"$target_model\" \
                                --attacker-model \"$attacker_model\" \
                                --target-base-url \"$target_base_url\" \
                                --attacker-base-url \"$attacker_base_url\" \
                                --target-temp $temp \
                                --attacker-temp $temp \
                                --turn-type \"$turn_type\""
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
