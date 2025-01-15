#!/bin/bash

# Define the values for each parameter
jailbreak_tactics=(
    # "opposite_day" 
    "crescendomation" 
    # "actor_attack" "acronym"
)
test_cases=(
    "how_to_make_meth" 
    # "figure_out_password"
    # "how_to_make_bomb" 
    # "racial_slurs"
)
target_models=(
    # "gpt-4o-mini-2024-07-18"
    # "meta-llama/llama-3.1-405b-instruct"
    # "meta-llama/llama-3.3-70b-instruct"
    "meta-llama/llama-3.2-1b-instruct"
)

# Static values
# attacker_model="gpt-4o"
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
                "--attacker-model \"$target_model\""
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
