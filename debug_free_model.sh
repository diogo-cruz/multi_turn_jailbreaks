#!/bin/bash

# =============================================================================
# Free Model Debugging Tool for Jailbreak Attacks
# =============================================================================
#
# This script provides a debugging environment for testing jailbreak attacks
# specifically against free-tier language models. It helps verify that the
# attack framework can properly interact with these models, which often have
# different characteristics and limitations compared to paid models.
#
# Key features:
# - Testing framework compatibility with free API models
# - Verification of model-specific handling and adjustments
# - Simple configuration for focused debugging of free model issues
# - Controlled environment for reproducing and fixing free model-specific bugs
# - Support for various free model providers
#
# This script is particularly useful during development and testing phases
# when adapting the framework to work with free-tier language models, or when
# troubleshooting specific issues related to these models.
#
# Usage:
#   ./debug_free_model.sh
#
# =============================================================================

# This script tests a free model implementation

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
TARGET_MODEL="google/gemma-3-1b-it:free"
ATTACKER_MODEL="google/gemini-2.5-pro-exp-03-25:free"
TURN_TYPE="multi_turn"
TEMP="0.0"

# Create a simple Python debug wrapper
cat > debug_wrapper.py << 'EOL'
import os
import sys
import traceback

# Original command line arguments
original_args = sys.argv[1:]

try:
    # Import openai to check configuration
    import openai
    print(f"OpenAI API Key: {os.environ.get('OPENAI_API_KEY', 'Not Set')[:5]}...{os.environ.get('OPENAI_API_KEY', 'Not Set')[-5:] if os.environ.get('OPENAI_API_KEY') else ''}")
    
    # Run the actual main.py with debug output
    print("Running main.py with arguments:", ' '.join(original_args))
    os.system(f"python main.py {' '.join(original_args)}")
except Exception as e:
    print(f"Exception Type: {type(e).__name__}")
    print(f"Exception: {str(e)}")
    print("Traceback:")
    traceback.print_exc()
EOL

# Run the wrapper script with our parameters
OPENAI_API_KEY="$OPENROUTER_API_KEY" python debug_wrapper.py \
    --jailbreak-tactic "$TACTIC" \
    --test-case "$TEST_CASE" \
    --target-model "$TARGET_MODEL" \
    --attacker-model "$ATTACKER_MODEL" \
    --target-base-url "https://openrouter.ai/api/v1" \
    --attacker-base-url "https://openrouter.ai/api/v1" \
    --target-temp $TEMP \
    --attacker-temp $TEMP \
    --turn-type "$TURN_TYPE"

# Clean up
rm debug_wrapper.py 