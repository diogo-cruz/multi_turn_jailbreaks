#!/bin/bash

# =============================================================================
# Jailbreak Testing Progress Tracker
# =============================================================================
#
# This utility script helps track the progress of jailbreak attack test runs
# by analyzing the results directory and providing comprehensive statistics
# on completed tests. It offers a quick way to monitor long-running parallel
# test batches and understand test coverage across different dimensions.
#
# Output includes:
# - Total number of completed test runs
# - Breakdown by jailbreak tactic
# - Breakdown by target model
# - Breakdown by test case
# - Breakdown by turn type (single-turn vs multi-turn)
# - List of most recent test runs
#
# This script is particularly useful when running large batches of tests with
# the parallel execution scripts to check progress and identify any gaps in
# test coverage.
#
# Usage:
#   ./check_completed_runs.sh
#
# =============================================================================

# Output directory
RESULTS_DIR="clean_results/strongreject_results"
TARGET_MODELS=("google/gemma-3-1b-it:free" "google/gemma-3-4b-it:free" "google/gemma-3-12b-it:free" "google/gemma-3-27b-it:free" "nvidia/llama-3.1-nemotron-nano-8b-v1:free" "nvidia/llama-3.3-nemotron-super-49b-v1:free" "nvidia/llama-3.1-nemotron-ultra-253b-v1:free" "meta-llama/llama-4-maverick:free" "meta-llama/llama-4-scout:free" "deepseek/deepseek-v3-base:free" "deepseek/deepseek-chat-v3-0324:free" "mistralai/mistral-small-3.1-24b-instruct:free" "mistralai/mixtral-8x7b-instruct:free")

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Results directory $RESULTS_DIR does not exist."
    exit 1
fi

# Count total results
total_results=$(find "$RESULTS_DIR" -name "*.jsonl" | wc -l)
echo "Total result files found: $total_results"

# Count by jailbreak tactic
echo -e "\nResults by jailbreak tactic:"
for tactic in $(find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;); do
    count=$(find "$RESULTS_DIR/$tactic" -name "*.jsonl" | wc -l)
    echo "$tactic: $count"
done

# Extract model names from filenames
echo -e "\nResults by model (from filenames):"
for model_pattern in "gemma-3-1b-it" "gemma-3-4b-it" "gemma-3-12b-it" "gemma-3-27b-it" "nemotron-nano-8b" "nemotron-super-49b" "nemotron-ultra-253b" "llama-4-maverick" "llama-4-scout" "deepseek-v3-base" "deepseek-chat-v3" "mistral-small" "mixtral-8x7b"; do
    count=$(find "$RESULTS_DIR" -name "*${model_pattern}*" | wc -l)
    echo "$model_pattern: $count"
done

# Count by test case (from filenames)
echo -e "\nResults by test case (from filenames):"
find "$RESULTS_DIR" -name "*.jsonl" | 
    sed -E 's|.*/[^_]+_([^_]+)_.*|\1|' | 
    sort | 
    uniq -c | 
    sort -nr

# Count by turn type (from filenames)
echo -e "\nResults by turn type (from filenames):"
for turn_type in "single_turn" "multi_turn"; do
    count=$(find "$RESULTS_DIR" -name "*${turn_type}*" | wc -l)
    echo "$turn_type: $count"
done

# Create a mapping file of completed combinations
echo -e "\nComparing to required models from script:"
tmp_dir=$(mktemp -d)
completed_file="${tmp_dir}/completed.txt"

# Generate list of completed runs (tactic, test case, model pattern, turn type)
for tactic in $(find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;); do
    for file in "$RESULTS_DIR/$tactic"/*.jsonl; do
        # Extract the meaningful parts from the filename
        filename=$(basename "$file")
        test_case=$(echo "$filename" | cut -d'_' -f2)
        
        # Extract the model pattern (this is tricky with the colons)
        for model_pattern in "gemma-3-1b-it" "gemma-3-4b-it" "gemma-3-12b-it" "gemma-3-27b-it" "nemotron-nano-8b" "nemotron-super-49b" "nemotron-ultra-253b" "llama-4-maverick" "llama-4-scout" "deepseek-v3-base" "deepseek-chat-v3" "mistral-small" "mixtral-8x7b"; do
            if [[ "$filename" == *"$model_pattern"* ]]; then
                # Extract turn type
                if [[ "$filename" == *"single_turn"* ]]; then
                    turn_type="single_turn"
                else
                    turn_type="multi_turn"
                fi
                
                # Add to completed list
                echo "$tactic|$test_case|$model_pattern|$turn_type" >> "$completed_file"
                break
            fi
        done
    done
done

# Count completed combinations for each model
echo -e "\nCompleted combinations by model:"
for model_pattern in "gemma-3-1b-it" "gemma-3-4b-it" "gemma-3-12b-it" "gemma-3-27b-it" "nemotron-nano-8b" "nemotron-super-49b" "nemotron-ultra-253b" "llama-4-maverick" "llama-4-scout" "deepseek-v3-base" "deepseek-chat-v3" "mistral-small" "mixtral-8x7b"; do
    for full_model in "${TARGET_MODELS[@]}"; do
        if [[ "$full_model" == *"$model_pattern"* ]]; then
            count=$(grep -c "$model_pattern" "$completed_file")
            echo "$full_model: $count combinations completed"
            break
        fi
    done
done

# Clean up
rm -rf "$tmp_dir"

# Show most recent runs
echo -e "\nMost recent 10 runs:"
find "$RESULTS_DIR" -name "*.jsonl" -printf "%T@ %p\n" | 
    sort -nr | 
    head -n 10 | 
    sed 's/[^ ]* //' | 
    xargs -I{} sh -c 'ls -la "{}" | cut -d" " -f6-'

echo -e "\nSample filenames with model names:"
find "$RESULTS_DIR" -name "*.jsonl" | head -n 5
