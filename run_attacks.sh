#!/bin/bash

# =============================================================================
# Single-Instance Jailbreak Attack Runner
# =============================================================================
#
# This script provides a simplified interface for running individual jailbreak 
# attack tests against language models. Unlike the parallel versions, this script
# executes a single attack configuration at a time, making it ideal for quick
# testing, debugging specific configurations, or when resources are limited.
#
# Key features:
# - Simple execution of a single jailbreak attack
# - Support for all implemented jailbreak tactics
# - Configurable target and attacker models
# - Detailed logging of the attack process
# - Compatibility with both single-turn and multi-turn attack modes
#
# This script is particularly useful when:
# - Testing a new jailbreak tactic implementation
# - Debugging issues with specific test cases
# - Running manual evaluations of individual tactics
# - Conserving API costs with targeted testing
#
# Usage:
#   ./run_attacks.sh [TACTIC] [TEST_CASE] [TARGET_MODEL] [ATTACKER_MODEL]
#
# =============================================================================

# Define the values for each parameter
jailbreak_tactics=(
    "crescendomation" 
    "actor_attack" 
    "acronym"
    "opposite_day" 
    "direct_request"
    "emotional_appeal"
    "command"
    "crowding"
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
    "meta-llama/llama-3.1-8b-instruct"
    "meta-llama/llama-3.1-70b-instruct"
    "meta-llama/llama-3.1-405b-instruct"
    "meta-llama/llama-3.2-1b-instruct"
    "meta-llama/llama-3.2-3b-instruct"
    "meta-llama/llama-3.3-70b-instruct"
    "gpt-4o-mini-2024-07-18"

)
temperatures=(
    # "0.0"
    "1.0"
)
turn_types=(
    "single_turn"
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

# Iterate through all combinations of parameters
for tactic in "${jailbreak_tactics[@]}"; do
    for test_case in "${test_cases[@]}"; do
        for target_model in "${target_models[@]}"; do
            for temp in "${temperatures[@]}"; do
                for turn_type in "${turn_types[@]}"; do
                    for attacker_model in "${attacker_models[@]}"; do
                        # Construct the command
                        command=(
                            "python main.py"
                            "--jailbreak-tactic \"$tactic\""
                            "--test-case \"$test_case\""
                            "--target-model \"$target_model\""
                            "--attacker-model \"$attacker_model\""
                            "--target-base-url \"$target_base_url\""
                            "--attacker-base-url \"$attacker_base_url\""
                            "--target-temp $temp"
                            "--attacker-temp $temp"
                            "--turn-type \"$turn_type\""
                        )

                        # Print the command (optional)
                        echo "Running: ${command[*]}"

                        # Execute the command
                        eval "${command[*]}"
                    done
                done
            done
        done
    done
done
