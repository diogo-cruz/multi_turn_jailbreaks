#!/bin/bash

# =============================================================================
# Rate Limit Debugging Tool for Jailbreak Attacks
# =============================================================================
#
# This script provides a debugging environment for testing the rate limiting
# functionality of the jailbreak attack framework. It allows researchers to
# verify that the rate limiting and error handling mechanisms work correctly
# when interacting with API services that have strict usage limits.
#
# Key features:
# - Simplified debugging of rate limit handling
# - Testing of exponential backoff functionality
# - Verification of error recovery mechanisms
# - Focused single-run configuration for easy issue isolation
# - Support for different model configurations
#
# This script is particularly useful during development and testing of the
# rate limit handling features, or when troubleshooting issues with API
# interactions that may be related to rate limiting.
#
# Usage:
#   ./debug_ratelimit.sh
#
# =============================================================================

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

echo "Testing rate-limited script with:"
echo "  Tactic: $TACTIC"
echo "  Test Case: $TEST_CASE"
echo "  Target Model: $TARGET_MODEL"
echo "  Attacker Model: $ATTACKER_MODEL"
echo "  Turn Type: $TURN_TYPE"
echo "  Temperature: $TEMP"
echo ""
echo "Running the test with rate limit handling..."

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