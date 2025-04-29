#!/bin/bash

# Load the API key from .env file
if [ -f .env ]; then
    source .env
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "Error: OPENROUTER_API_KEY not found in .env file."
        exit 1
    fi
    export OPENAI_API_KEY="$OPENROUTER_API_KEY"
else
    echo "Error: .env file not found. Please create it with your OPENROUTER_API_KEY."
    exit 1
fi

echo "API Key loaded: ${OPENROUTER_API_KEY:0:5}...${OPENROUTER_API_KEY: -5}"

# Set up the parameters for a single test
TACTIC="crescendomation"
TEST_CASE="non_violent_crimes_2_alt1"
TARGET_MODEL="mistralai/mixtral-8x7b-instruct:free"
ATTACKER_MODEL="mistralai/mixtral-8x7b-instruct:free"
TURN_TYPE="multi_turn"
TEMP="0.0"

echo "Testing fixed rate-limited script with:"
echo "  Tactic: $TACTIC"
echo "  Test Case: $TEST_CASE"
echo "  Target Model: $TARGET_MODEL"
echo "  Attacker Model: $ATTACKER_MODEL"
echo "  Turn Type: $TURN_TYPE"
echo "  Temperature: $TEMP"
echo ""
echo "Running the test with improved rate limit handling and NoneType fix..."

# Run the rate-limited version with our parameters
OPENAI_API_KEY="$OPENROUTER_API_KEY" python main_ratelimit.py \
    --jailbreak-tactic "$TACTIC" \
    --test-case "$TEST_CASE" \
    --target-model "$TARGET_MODEL" \
    --attacker-model "$ATTACKER_MODEL" \
    --target-base-url "https://openrouter.ai/api/v1" \
    --attacker-base-url "https://openrouter.ai/api/v1" \
    --target-temp $TEMP \
    --attacker-temp $TEMP \
    --turn-type "$TURN_TYPE" 