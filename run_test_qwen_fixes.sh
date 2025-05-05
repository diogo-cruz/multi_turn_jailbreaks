#!/bin/bash
# This script tests the fixes for Qwen 3 reasoning extraction

# Make a new output folder for these tests
TEST_FOLDER="batch_qwen_fix_test"

# Test with Qwen 3 small model (free tier)
echo "Testing Qwen 3 0.6b model with reasoning..."
python main.py \
  --target-model "qwen/qwen3-0.6b-04-28:free" \
  --target-temp 0.0 \
  --attacker-model "openai/gpt-4o-mini" \
  --attacker-temp 1.0 \
  --evaluator-model "openai/gpt-4o-mini" \
  --test-case "remove_watermarks" \
  --turn-type "multi_turn" \
  --jailbreak-tactic "direct_request" \
  --output-folder "$TEST_FOLDER" \
  --samples 1 \
  --reasoning "high"

# Test with Qwen 3 8b model
echo "Testing Qwen 3 8b model with reasoning..."
python main.py \
  --target-model "qwen/qwen3-8b" \
  --target-temp 0.0 \
  --attacker-model "openai/gpt-4o-mini" \
  --attacker-temp 1.0 \
  --evaluator-model "openai/gpt-4o-mini" \
  --test-case "remove_watermarks" \
  --turn-type "multi_turn" \
  --jailbreak-tactic "direct_request" \
  --output-folder "$TEST_FOLDER" \
  --samples 1 \
  --reasoning "high"

# Test with DeepSeek R1 for comparison
echo "Testing DeepSeek R1 model with reasoning..."
python main.py \
  --target-model "deepseek/deepseek-r1" \
  --target-temp 0.0 \
  --attacker-model "openai/gpt-4o-mini" \
  --attacker-temp 1.0 \
  --evaluator-model "openai/gpt-4o-mini" \
  --test-case "remove_watermarks" \
  --turn-type "multi_turn" \
  --jailbreak-tactic "direct_request" \
  --output-folder "$TEST_FOLDER" \
  --samples 1 \
  --reasoning "high"

echo "Test runs completed. Check results in clean_results/final_runs/$TEST_FOLDER/" 