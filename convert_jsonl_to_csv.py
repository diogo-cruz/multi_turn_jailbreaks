#!/usr/bin/env python3
"""
Convert the human evaluations JSONL file to CSV format.
"""

import json
import pandas as pd

def convert_jsonl_to_csv():
    """Convert false_positive_annotations.jsonl to CSV format."""
    
    data = []
    
    with open('clean_results/false_positive_annotations.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save as CSV
    df.to_csv('false_positive_annotations.csv', index=False)
    
    print(f"Converted {len(data)} records from JSONL to CSV")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample records:")
    print(df.head())

if __name__ == "__main__":
    convert_jsonl_to_csv()