#!/bin/bash

# Define the values for each parameter
jailbreak_tactics=(
    # "opposite_day" 
    # "crescendomation" 
    # "actor_attack" 
    # "acronym"
    # "allegory"
    # "appeal_to_authority"
    # "command"
    "direct_request"
)
test_cases=(
    "academic_integrity"
    "child_exploitation"
    "corporate_secretes"
    "cybersecurity_exploits"
    "election_interference"
    "extremist_content"
    "figure_out_password"
    "financial_fraud"
    "how_to_make_meth" 
    "how_to_make_bomb"
    "human_trafficking"
    "identity_theft"
    "medical_privacy"
    "racial_slurs"
    "misinformation_annexation_of_crimea_russia"
)
target_models=(
    # "gpt-4o-mini-2024-07-18"
    # "meta-llama/llama-3.1-405b-instruct"
    # "meta-llama/llama-3.3-70b-instruct"
    # "meta-llama/llama-3.2-1b-instruct"
    "meta-llama/llama-3.1-8b-instruct"
    "meta-llama/llama-3.1-70b-instruct"
    "meta-llama/llama-3.2-3b-instruct"
)

# Static values
attacker_model="gpt-4o-mini-2024-07-18"
target_base_url="https://openrouter.ai/api/v1"
attacker_base_url="https://openrouter.ai/api/v1"

# Iterate through all combinations of parameters
for tactic in "${jailbreak_tactics[@]}"; do
    for test_case in "${test_cases[@]}"; do
        for target_model in "${target_models[@]}"; do
            # Construct the command
            command=(
                "python main.py"
                "--jailbreak-tactic \"$tactic\""
                "--test-case \"$test_case\""
                "--target-model \"$target_model\""
                "--attacker-model \"$attacker_model\""
                "--target-base-url \"$target_base_url\""
                "--attacker-base-url \"$attacker_base_url\""
            )

            # Print the command (optional)
            echo "Running: ${command[*]}"

            # Execute the command
            eval "${command[*]}"
        done
    done
done
