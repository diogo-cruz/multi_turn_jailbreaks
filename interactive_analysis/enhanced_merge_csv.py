import pandas as pd
import os
import glob

def enhanced_merge_csv_files():
    """
    Merge all CSV files in the current directory except model_comparison.csv and master_data.csv
    into a single master CSV file. Add attacker_model and evaluator_model columns, and remove the
    Unnamed: 0 column.
    """
    # Get all CSV files in the directory
    csv_files = glob.glob('*.csv')
    
    # Remove files we don't want to merge
    files_to_exclude = ['model_comparison.csv', 'master_data.csv', 'enhanced_master_data.csv']
    for exclude_file in files_to_exclude:
        if exclude_file in csv_files:
            csv_files.remove(exclude_file)
    
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
        
        # Add attacker_model and evaluator_model columns based on source file
        if file == 'results_2D.csv':
            current_df['attacker_model'] = 'gpt-4o-mini-2024-07-18'
            current_df['evaluator_model'] = 'anthropic/claude-3-haiku'
        elif file == 'results_2D_2.csv':
            current_df['attacker_model'] = 'gpt-4o-mini-2024-07-18'
            current_df['evaluator_model'] = 'openai/gpt-4.1-mini'
        else:
            current_df['attacker_model'] = 'gpt-4o-mini-2024-07-18'
            current_df['evaluator_model'] = 'gpt-4o-mini-2024-07-18'
        
        # Append to the combined dataframe
        combined_df = pd.concat([combined_df, current_df], ignore_index=True)
    
    # Remove the Unnamed: 0 column if it exists
    if 'Unnamed: 0' in combined_df.columns:
        combined_df = combined_df.drop('Unnamed: 0', axis=1)
    
    # Reorder columns to place attacker_model and evaluator_model after target_model
    cols = list(combined_df.columns)
    target_model_index = cols.index('target_model')
    
    # Create the new column order
    new_cols = cols[:target_model_index+1] + ['attacker_model', 'evaluator_model'] + [col for col in cols[target_model_index+1:] if col not in ['attacker_model', 'evaluator_model']]
    
    # Reorder the dataframe
    combined_df = combined_df[new_cols]
    
    # Save the combined dataframe to a new CSV file
    output_file = 'enhanced_master_data.csv'
    combined_df.to_csv(output_file, index=False)
    
    print(f"Successfully merged {len(csv_files)} files into {output_file}")
    print(f"Total rows in merged file: {len(combined_df)}")
    print(f"Columns in the merged file: {list(combined_df.columns)}")

if __name__ == "__main__":
    enhanced_merge_csv_files() 