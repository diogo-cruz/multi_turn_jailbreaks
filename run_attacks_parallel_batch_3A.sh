#!/bin/bash

# Number of parallel processes to run
THREAD_COUNT=1
# attacker temperature
ATTACK_TEMP=1.0

# If you need multiple samples of the same combination, set that here
SAMPLES=1

# Output folder name
OUTPUT_FOLDER="batch3A"

# Define the values for each parameter
jailbreak_tactics=(
    # "crescendomation" 
    # "actor_attack" 
    # "crescendomation" 
    # "actor_attack" 
    # "acronym"
    # "opposite_day" 
    # "opposite_day" 
    "direct_request"   
    # "emotional_appeal"
    # "command"
    # "crowding"
    #"allegory"
    #"appeal_to_authority"
)
test_cases=(
    ### filtered StrongREJECT ###
    # stealing_credit_card_info   # exclude?
    # sql_injection   # exclude?
    # car_break-in   # exclude?
    fake_online_profile
    # store_theft
    date_rape_drug
    # nudes_blackmail
    # illegal_brothel   # exclude?
    airbnb_voyeurism
    # bestiality   # exclude?
    # mass_shooting_plan   # exclude?
    # poisoning_water_supply
    terrorist_recruitment
    # threatening_letter   # exclude?
    # bus_bomb_placement

    ### Disinformation and deception
    # "deceptive_email"
    "remove_watermarks"             # done 
    # "tax_fraud"
    "drunk_driving"               # done
    # "bomb_threats"  # exclude?

    ### Hate, harassment and discrimination
    # "hate_speech_immigrants"
    "false_accusation"             # done
    # "asian_insults"  # exclude?
    # "gender_insults"
    "lgbtq_insults"                 # done 

    ### Illegal goods and services
    # "illegal_arms"
    "counterfeit_money"          # done 
    # "deoderant_flamethrower"
    "pistol_serial_numbers"        # done 
    # "improvised_gun"


    ### OLD StrongREJECT ###
    # "deoderant_flamethrower"
    # "disarm_police"
    # "hate_speech"
    # "leak_photos"
    # "steal_info"
    # "women_drivers"

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
    # "meta-llama/llama-3.2-1b-instruct"   # not using
    # "meta-llama/llama-3.2-3b-instruct"   # not using
    # "meta-llama/llama-3.2-1b-instruct"   # not using
    # "meta-llama/llama-3.2-3b-instruct"   # not using
    # "anthropic/claude-3.7-sonnet"        # use later
    # "openai/gpt-4o-latest"             # use later
    # "meta-llama/llama-3.1-8b-instruct"
    # "meta-llama/llama-3.1-70b-instruct"
    # "meta-llama/llama-3.1-405b-instruct"
    # "meta-llama/llama-3.3-70b-instruct"
    # "gpt-4o-mini-2024-07-18"
    # "meta-llama/llama-3.1-405b-instruct"
    # "meta-llama/llama-3.3-70b-instruct"
    # "gpt-4o-mini-2024-07-18"
    # "deepseek/deepseek-chat-v3-0324"
    # "deepseek/deepseek-r1"
    # "openai/o3-mini-high"
    # "qwen/qwen-2.5-7b-instruct"
    # "qwen/qwen2.5-32b-instruct"
    # "qwen/qwen-2.5-72b-instruct"
    # "google/gemini-2.0-flash-001"
    # "google/gemini-2.0-flash-lite-001"
    # "google/gemini-flash-1.5"
    # "anthropic/claude-3-haiku"
    # "google/gemma-2-9b-it"
    # "google/gemma-3-12b-it"
    # "google/gemma-3-27b-it"
    # "mistralai/mistral-nemo"
    # "mistralai/mistral-tiny"
    # "mistralai/mistral-small-3.1-24b-instruct"
    # "mistralai/mistral-7b-instruct-v0.3"
    # "meta-llama/llama-4-maverick"
    # "meta-llama/llama-4-scout"
    # "x-ai/grok-3-mini-beta"

    ### new models
    # "deepseek/deepseek-chat-v3-0324"
    # "google/gemini-2.5-pro-preview-03-25"
    "google/gemini-2.5-flash-preview"
    "anthropic/claude-3.5-sonnet"
    "anthropic/claude-3.7-sonnet"
    "openai/gpt-4o"
    "openai/gpt-4.1"
    "openai/gpt-4.1-mini"
    "openai/gpt-4.1-nano"
)
temperatures=(
    "0.0"
    # "1.0"
)
turn_types=(
    "single_turn"
    "multi_turn"
)

attacker_models=(
    # "openai/gpt-4.1-nano"
    "openai/gpt-4o-mini"
    # "gpt-4o-mini-2024-07-18"
    # "anthropic/claude-3-haiku"
    # "google/gemini-2.0-flash-lite-001"
    # "google/gemini-2.0-flash-001"
    # "cognitivecomputations/dolphin-mixtral-8x7b"
    #"cohere/command-r-plus"
    #"nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
)

# Static values
target_base_url="https://openrouter.ai/api/v1"
attacker_base_url="https://openrouter.ai/api/v1"

# Evaluator
evaluator_model="openai/gpt-4.1-mini"
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
                                --attacker-temp $ATTACK_TEMP \
                                --turn-type \"$turn_type\"" \
                                --samples $SAMPLES \
                                --evaluator-model \"$evaluator_model\" \
                                --evaluator-temp $evaluator_temp \
                                --output-folder \"$OUTPUT_FOLDER\"
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
