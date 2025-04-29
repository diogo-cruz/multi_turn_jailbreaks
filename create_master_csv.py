"""
Master CSV Generator for Jailbreak Attack Analysis

This script aggregates evaluation results from multiple jailbreak attack runs into
a consolidated master CSV file. It processes evaluation data from various models,
tactics, and test cases, organizing them into a standardized format for easier
analysis and visualization.

Features:
- Recursive scanning of evaluation result directories
- Extraction of key metrics from evaluation JSON files
- Consolidation of results by model, tactic, test case, and other dimensions
- Calculation of aggregate statistics (success rates, average scores, etc.)
- Export to CSV format for compatibility with analysis tools and dashboards
- Support for filtering and transformation of result data

The generated master CSV serves as the primary dataset for subsequent analysis
scripts, visualization tools, and correlation studies. It provides a comprehensive
view of jailbreak attack effectiveness across different experimental conditions.

Usage:
    python create_master_csv.py [options]

Output files are saved to the csv_results directory by default.
"""

from pathlib import Path
import pandas as pd
import subprocess
import os
import sys
import re

def extract_evaluator_model(filename, batch_name):
    # Check if "eval" is in the filename
    eval_match = re.search(r'_eval_([^\.]+)', filename)
    if eval_match:
        # Get the model name after "eval_"
        evaluator = eval_match.group(1)
        
        # Fix issue with "eval_gpt-4.1-nano"
        if "gpt-4.1-nano" in evaluator:
            return "openai/gpt-4.1-nano"
        # Handle specific evaluator models
        elif evaluator == "gpt-4o-mini":
            return "openai/gpt-4o-mini-2024-07-18"
        elif evaluator.startswith("gpt-"):
            return f"openai/{evaluator}"
        elif any(prefix in evaluator for prefix in ["claude-", "llama-", "deepseek-", "gemini-"]):
            # These models likely have vendors that should be preserved
            if evaluator.startswith("claude-"):
                return f"anthropic/{evaluator}"
            elif evaluator.startswith("llama-"):
                return f"meta-llama/{evaluator}"
            elif evaluator.startswith("deepseek-"):
                return f"deepseek/{evaluator}"
            elif evaluator.startswith("gemini-"):
                return f"google/{evaluator}"
            return evaluator
        else:
            # Default to openai/ prefix for unknown models
            return f"openai/{evaluator}"
    
    # For batch3A, use gpt-4.1-mini as default
    if batch_name == "batch3A":
        return "openai/gpt-4.1-mini"
    # For other batches, use gpt-4o-mini-2024-07-18
    return "openai/gpt-4o-mini-2024-07-18"

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
                
                # Collect original JSONL filenames
                jsonl_files = list(subfolder.glob('**/*.jsonl'))
                
                # Create a mapping of test case + model + turn type to filename
                file_mapping = {}
                for file_path in jsonl_files:
                    file_name = file_path.name
                    components = file_name.split('_')
                    
                    # Skip if the filename doesn't have enough components
                    if len(components) < 4:
                        continue
                    
                    # Extract components from filename
                    tactic = components[0]
                    test_case = components[1]
                    
                    # Find the model part (could be in different positions)
                    model_idx = -1
                    for i, part in enumerate(components):
                        if any(model_prefix in part for model_prefix in ["gpt", "claude", "llama", "deepseek", "gemini"]):
                            model_idx = i
                            break
                    
                    if model_idx == -1:
                        continue
                        
                    model = components[model_idx]
                    
                    # Find turn type (single or multi)
                    turn_type = "single" if "single" in file_name else "multi" if "multi" in file_name else None
                    if not turn_type:
                        continue
                    
                    key = (tactic, test_case, model, turn_type)
                    file_mapping[key] = file_path
                
                # Add source_file, attacker_model, and evaluator_model columns
                source_files = []
                attacker_models = []
                evaluator_models = []
                
                for _, row in df.iterrows():
                    tactic = row.get('jailbreak_tactic', '')
                    test_case = row.get('test_case', '')
                    model = row.get('target_model', '').split('/')[-1] if '/' in row.get('target_model', '') else row.get('target_model', '')
                    turn_type = row.get('turn_type', '')
                    
                    key = (tactic, test_case, model, turn_type)
                    
                    # Find matching file
                    matched_file = None
                    for file_key, file_path in file_mapping.items():
                        if all(k in str(file_path) for k in [tactic, test_case, model.replace('/', '-'), turn_type]):
                            matched_file = file_path
                            break
                    
                    # Set source_file
                    if matched_file:
                        source_files.append(matched_file.name)
                        evaluator_models.append(extract_evaluator_model(matched_file.name, batch_name))
                    else:
                        source_files.append(None)
                        # Default evaluator model based on batch
                        if batch_name == "batch3A":
                            evaluator_models.append("openai/gpt-4.1-mini")
                        else:
                            evaluator_models.append("openai/gpt-4o-mini-2024-07-18")
                    
                    # Set attacker_model (default to gpt-4o-mini-2024-07-18)
                    attacker_models.append("openai/gpt-4o-mini-2024-07-18")
                
                # Add the columns to the DataFrame
                df['source_file'] = source_files
                df['attacker_model'] = attacker_models
                df['evaluator_model'] = evaluator_models
                
                # Ensure the DataFrame has the required columns
                # Based on enhanced_master_data.csv structure
                required_columns = [
                    "jailbreak_tactic", "test_case", "turn_type", "target_model",
                    "target_temp", "max_round", "goal_achieved", "scores", 
                    "refused", "timestamp", "batch", "source_file", "attacker_model", "evaluator_model"
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
        
        # Save the master CSV
        master_csv_path = csv_results_dir / "master_results.csv"
        master_df.to_csv(master_csv_path, index=False)
        print(f"Created master CSV file: {master_csv_path}")
        print(f"Total rows: {len(master_df)}")
    else:
        print("No data to combine. Check for errors above.")

if __name__ == "__main__":
    main() 