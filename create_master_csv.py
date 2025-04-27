from pathlib import Path
import pandas as pd
import subprocess
import os
import sys

def main():
    # Define paths
    base_dir = Path('.')
    final_runs_dir = base_dir / "clean_results" / "final_runs"
    csv_results_dir = base_dir / "csv_results"
    
    # Create csv_results directory if it doesn't exist
    csv_results_dir.mkdir(exist_ok=True)
    
    # List all subfolders in final_runs
    subfolders = [f for f in final_runs_dir.iterdir() if f.is_dir()]
    
    all_dfs = []
    
    for subfolder in subfolders:
        batch_name = subfolder.name
        print(f"Processing {batch_name}...")
        
        # Generate CSV for this subfolder
        output_csv = f"{batch_name}_results.csv"
        cmd = f"python plot_scripts/create_csv.py --results-dir {subfolder} --csv {output_csv}"
        
        # Run the command
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"Generated {output_csv}")
            
            # Read the generated CSV
            csv_path = csv_results_dir / output_csv
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                
                # Add batch column
                df['batch'] = batch_name
                
                # Ensure the DataFrame has the required columns
                # Based on enhanced_master_data.csv structure
                required_columns = [
                    "jailbreak_tactic", "test_case", "turn_type", "target_model",
                    "target_temp", "max_round", "goal_achieved", "scores", 
                    "refused", "timestamp", "batch"
                ]
                
                # Add missing columns with None values
                for col in required_columns:
                    if col not in df.columns and col != 'batch':
                        df[col] = None
                
                all_dfs.append(df)
            else:
                print(f"Warning: {csv_path} was not created")
        except subprocess.CalledProcessError as e:
            print(f"Error processing {batch_name}: {e}")
    
    if all_dfs:
        # Combine all DataFrames
        master_df = pd.concat(all_dfs, ignore_index=True)
        
        # Add empty columns for attacker_model, evaluator_model, and source_file if not present
        required_enhanced_columns = [
            "attacker_model", "evaluator_model", "source_file"
        ]
        
        for col in required_enhanced_columns:
            if col not in master_df.columns:
                master_df[col] = None
        
        # Save the master CSV
        master_csv_path = csv_results_dir / "master_results.csv"
        master_df.to_csv(master_csv_path, index=False)
        print(f"Created master CSV file: {master_csv_path}")
        print(f"Total rows: {len(master_df)}")
    else:
        print("No data to combine. Check for errors above.")

if __name__ == "__main__":
    main() 