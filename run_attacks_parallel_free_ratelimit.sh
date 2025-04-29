#!/bin/bash

# Number of parallel processes to run (reduced from original to prevent too many concurrent requests)
THREAD_COUNT=32

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
    "mistralai/mistral-small-3.1-24b-instruct:free"
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
                            # Skip if jailbreak tactic doesn't have single turn and turn_type is single_turn
                            if [[ "$turn_type" == "single_turn" ]]; then
                                # Check if the tactic has a single turn implementation
                                if ! grep -q "def single_turn" "jailbreaks/$tactic/run.py" 2>/dev/null; then
                                    continue
                                fi
                            fi
                            
                            # Use the rate-limited version of the main script
                            echo "OPENAI_API_KEY=\"$OPENROUTER_API_KEY\" python main_ratelimit.py \
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
echo "Using OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:5}...${OPENROUTER_API_KEY: -5}"
echo "Using rate-limited script with automatic retry mechanism"

# Run with progress tracking
generate_commands | parallel -j "$THREAD_COUNT" --bar --colsep ' ' {} 