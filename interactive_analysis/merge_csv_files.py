import pandas as pd
import os
import glob

def merge_csv_files():
    """
    Merge all CSV files in the current directory except model_comparison.csv
    into a single master CSV file.
    """
    # Get all CSV files in the directory
    csv_files = glob.glob('*.csv')
    
    # Remove model_comparison.csv from the list if it exists
    if 'model_comparison.csv' in csv_files:
        csv_files.remove('model_comparison.csv')
    
    if not csv_files:
        print("No CSV files found to merge.")
        return
    
    print(f"Found {len(csv_files)} CSV files to merge: {csv_files}")
    
    # Initialize an empty dataframe to store the combined data
    combined_df = pd.DataFrame()
    
    # Process each CSV file
    for file in csv_files:
        print(f"Processing {file}...")
        # Read the current CSV file
        current_df = pd.read_csv(file)
        
        # Add a source column to track which file the data came from
        current_df['source_file'] = file
        
        # Append to the combined dataframe
        combined_df = pd.concat([combined_df, current_df], ignore_index=True)
    
    # Save the combined dataframe to a new CSV file
    output_file = 'master_data.csv'
    combined_df.to_csv(output_file, index=False)
    
    print(f"Successfully merged {len(csv_files)} files into {output_file}")
    print(f"Total rows in merged file: {len(combined_df)}")

if __name__ == "__main__":
    merge_csv_files() 