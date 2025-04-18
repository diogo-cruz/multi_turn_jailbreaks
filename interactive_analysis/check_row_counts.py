import pandas as pd
import glob
import os

def check_row_counts():
    # Get all CSV files in the directory
    csv_files = glob.glob('*.csv')
    
    # Remove enhanced_master_data.csv from the list for our count check
    files_to_exclude = ['model_comparison.csv', 'master_data.csv']
    source_files = [file for file in csv_files if file not in files_to_exclude]
    
    # Get row count of merged file
    if 'enhanced_master_data.csv' in csv_files:
        merged_df = pd.read_csv('enhanced_master_data.csv')
        merged_row_count = len(merged_df)
        print(f"Row count in enhanced_master_data.csv: {merged_row_count}")
    else:
        print("enhanced_master_data.csv not found.")
        return
    
    # Calculate total rows in source files
    total_source_rows = 0
    file_counts = {}
    
    for file in source_files:
        if file == 'enhanced_master_data.csv':
            continue
        df = pd.read_csv(file)
        row_count = len(df)
        file_counts[file] = row_count
        total_source_rows += row_count
        print(f"Row count in {file}: {row_count}")
    
    print(f"\nTotal rows in source files: {total_source_rows}")
    print(f"Rows in merged file: {merged_row_count}")
    
    if total_source_rows == merged_row_count:
        print("✓ Row counts match!")
    else:
        print(f"✗ Row counts don't match. Difference: {merged_row_count - total_source_rows}")
        
        # Check if any files in the merged data aren't in our count
        if 'source_file' in merged_df.columns:
            merged_sources = merged_df['source_file'].unique()
            for source in merged_sources:
                if source not in file_counts:
                    print(f"Note: {source} appears in the merged data but wasn't counted in our check")
                    count = len(merged_df[merged_df['source_file'] == source])
                    print(f"  This file contributes {count} rows to the merged data")

if __name__ == "__main__":
    check_row_counts() 