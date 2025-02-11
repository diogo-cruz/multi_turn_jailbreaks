#!/bin/bash

# Find all JSONL files in the results directory
find results -name "*.jsonl" | sort > all_jsonl.txt

# Find all analysis files in the results directory
find results -name "*_analysis.md" | sort > all_analysis.txt

# Process JSONL files to extract base names
while IFS= read -r file; do
    # Extract base name by removing .jsonl extension
    base_name="${file%.jsonl}"
    echo "$base_name|$file" >> processed_jsonl.txt
done < all_jsonl.txt

# Process analysis files to extract base names
while IFS= read -r file; do
    # Extract base name by removing _analysis.md extension
    base_name="${file%_analysis.md}"
    echo "$base_name" >> processed_analysis.txt
done < all_analysis.txt

echo "Files that need analysis:"

# Create a temporary file with unique unanalyzed entries
awk -F'|' 'NR==FNR{analyzed[$1]=1; next} !analyzed[$1] && !seen[$1]++{print $2}' processed_analysis.txt processed_jsonl.txt > unanalyzed_unique.txt

# Randomly select 4 lines using shuf
shuf -n 4 unanalyzed_unique.txt

# Clean up temporary files
rm all_jsonl.txt all_analysis.txt processed_jsonl.txt processed_analysis.txt unanalyzed_unique.txt