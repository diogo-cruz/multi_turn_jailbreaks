#!/bin/bash

# =============================================================================
# Jailbreak Results Preprocessing Script
# =============================================================================
#
# This script automates the preprocessing of jailbreak attack result files 
# before they are analyzed. It handles synchronization of results from external
# storage, file organization, and filename normalization to ensure consistent
# analysis.
#
# The script:
# - Creates necessary directory structure for results
# - Syncs results from Google Drive using rclone
# - Copies all JSONL files to a unified results directory
# - Standardizes filenames by converting deterministic tags to timestamps
# - Removes special characters and model name artifacts from filenames
# - Eliminates duplicate files to prevent analysis errors
# 
# This preprocessing step is essential for ensuring consistent file naming
# conventions and organization before detailed analysis is performed.
#
# Usage:
#   ./preprocess_results.sh
#
# =============================================================================

# Create results directory if it doesn't exist
mkdir -p results
mkdir -p results_direct

# Sync results from Google Drive
echo "Syncing results from Google Drive..."
# rclone copy "mydrive:AISC10/Multi-turn Jailbreaks Project/Jailbreak results" ./results_direct
rclone copy "mydrive:Multi-turn Jailbreaks Project/Jailbreak results" ./results_direct

# Copy all jsonl files from results_direct to results
cp results_direct/*/*.jsonl results/

# Change to results directory and rename files with deterministic pattern
cd results && find . -type f -name "*deterministic*.jsonl" | perl -e 'while(<>){chomp;$old=$_;if(s/deterministic\.jsonl$/2024-02-05_01:00:00.jsonl/ || s/deterministic(\d+)\.jsonl$/2024-02-05_0$1:00:00.jsonl/){rename $old,$_ if -e $old;}}'

# Convert - and : to _ in filenames

echo "Converting special characters and removing model names from filenames..."
find . -type f -name "*.jsonl" | while read file; do
    # Use a single sed command without -e flags
    newname=$(echo "$file" | sed '
        s/gpt-4o-mini-2024-07-18//g
        s/_llama_3.1_8b_instruct//g
        s/_llama_3.1_70b_instruct//g
        s/_llama_3.1_405b_instruct//g
        s/_llama_3.2_1b_instruct//g
        s/_llama_3.2_3b_instruct//g
        s/_llama_3.3_70b_instruct//g
        s/[-:]/_/g
        s/__*/_/g
        s/_\././g')

    if [ "$file" != "$newname" ] && [ ! -z "$newname" ]; then
        if [ -f "$newname" ]; then
            rm "$file"
            #echo "Removed duplicate file: $file"
        else
            mv "$file" "$newname"
            #echo "Renamed: $file -> $newname"
        fi
    fi
done

echo "Preprocessing completed successfully!"