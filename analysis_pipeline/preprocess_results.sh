#!/bin/bash

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