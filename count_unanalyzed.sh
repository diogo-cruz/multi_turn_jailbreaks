#!/bin/bash

# Find all JSONL files in the results directory
find results -name "*.jsonl" | sort > all_jsonl.txt

# Find all analysis files in the results directory
find results -name "*_analysis.md" | sort > all_analysis.txt

# Create temporary files to store processed names
> processed_jsonl.txt
> processed_analysis.txt

# Process JSONL files to extract base names (everything before turn_)
while IFS= read -r file; do
    # Extract base name by taking everything up to "turn_"
    base_name=$(echo "$file" | sed -E 's/^(.*turn)_.*/\1/')
    echo "$base_name|$file" >> processed_jsonl.txt
done < all_jsonl.txt

# Process analysis files to extract base names (everything before turn_)
while IFS= read -r file; do
    # Extract base name by taking everything up to "turn_"
    base_name=$(echo "$file" | sed -E 's/^(.*turn)_.*/\1/')
    echo "$base_name" >> processed_analysis.txt
done < all_analysis.txt

# Find unanalyzed base names
sort processed_analysis.txt | uniq > analyzed_bases.txt
sort -t'|' -k1,1 processed_jsonl.txt > sorted_jsonl.txt

# Count unique unanalyzed base names
total_count=$(awk -F'|' 'NR==FNR{analyzed[$1]=1; next} !analyzed[$1] && !seen[$1]++{count++} END{print count}' analyzed_bases.txt sorted_jsonl.txt)

echo "Total number of unique unanalyzed tactic/test/turn combinations: $total_count"

# Also show the full list of unique base names that need analysis
echo -e "\nUnique tactic/test/turn combinations that need analysis:"
awk -F'|' 'NR==FNR{analyzed[$1]=1; next} !analyzed[$1] && !seen[$1]++{print $1}' analyzed_bases.txt sorted_jsonl.txt | sort

# Clean up temporary files
rm all_jsonl.txt all_analysis.txt processed_jsonl.txt processed_analysis.txt analyzed_bases.txt sorted_jsonl.txt 