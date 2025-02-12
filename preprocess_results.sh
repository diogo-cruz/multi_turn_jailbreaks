#!/bin/bash

# Create results directory if it doesn't exist
mkdir -p results
mkdir -p results_direct

# Sync results from Google Drive
echo "Syncing results from Google Drive..."
rclone copy "mydrive:AISC10/Multi-turn Jailbreaks Project/Jailbreak results" ./results_direct

# Copy all jsonl files from results_direct to results
cp results_direct/*/*.jsonl results/

# Change to results directory and rename files with deterministic pattern
cd results && find . -type f -name "*deterministic*.jsonl" | perl -e 'while(<>){chomp;$old=$_;if(s/deterministic\.jsonl$/2024-02-05_01:00:00.jsonl/ || s/deterministic(\d+)\.jsonl$/2024-02-05_0$1:00:00.jsonl/){rename $old,$_ if -e $old;}}'

# Convert - and : to _ in filenames
echo "Converting special characters in filenames..."
find . -type f -name "*.jsonl" | while read file; do
    newname=$(echo "$file" | sed 's/[-:]/_/g')
    if [ "$file" != "$newname" ]; then
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