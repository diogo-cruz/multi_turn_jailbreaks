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
import json

def read_jsonl_for_info(file_path):
    """
    Read the JSONL file and extract evaluator_model, original_evaluator_model, and reasoning information.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        tuple: (evaluator_model, original_evaluator_model, reasoning)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            evaluator_model = None
            original_evaluator_model = None
            reasoning = None
            
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Get evaluator model info if not already found
                    if not evaluator_model and data.get('evaluator_model'):
                        evaluator_model = data.get('evaluator_model')
                        original_evaluator_model = data.get('original_evaluator_model')
                    
                    # Get reasoning if present
                    if reasoning is None and 'reasoning' in data:
                        reasoning_value = data.get('reasoning')
                        # Only use reasoning if it's a string and not None
                        if isinstance(reasoning_value, str):
                            reasoning = reasoning_value
                except json.JSONDecodeError:
                    continue
            
            return evaluator_model, original_evaluator_model, reasoning
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    # Return None if we couldn't find the information
    return None, None, None

def extract_evaluator_model_from_filename(filename, batch_name):
    """
    Extract evaluator model from filename when JSONL data is not available.
    This is the fallback method.
    """
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
    interactive_analysis_dir = base_dir / "interactive_analysis" / "public"
    evaluator_analysis_dir = base_dir / "evaluator_analysis" / "public"
    
    # Create directories if they don't exist
    csv_results_dir.mkdir(exist_ok=True)
    interactive_analysis_dir.mkdir(parents=True, exist_ok=True)
    evaluator_analysis_dir.mkdir(parents=True, exist_ok=True)
    
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
                
                # Add source_file, attacker_model, evaluator_model, original_evaluator_model, and reasoning columns
                source_files = []
                attacker_models = []
                evaluator_models = []
                original_evaluator_models = []
                reasonings = []
                
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
                    
                    # Set source_file, evaluator models, and reasoning
                    if matched_file:
                        source_files.append(matched_file.name)
                        
                        # Try to extract information from the JSONL file
                        eval_model, orig_eval_model, reasoning = read_jsonl_for_info(matched_file)
                        
                        # Add reasoning
                        reasonings.append(reasoning)
                        
                        if eval_model:
                            # Use values from JSONL if available
                            evaluator_models.append(eval_model)
                            if orig_eval_model:
                                original_evaluator_models.append(orig_eval_model)
                            else:
                                # If original not present, use the same as evaluator_model
                                original_evaluator_models.append(eval_model)
                        else:
                            # Fall back to filename-based extraction if JSONL doesn't have the info
                            current_evaluator_model = extract_evaluator_model_from_filename(matched_file.name, batch_name)
                            evaluator_models.append(current_evaluator_model)
                            
                            # Store the original evaluator model from the filename
                            eval_match = re.search(r'_eval_([^\.]+)', matched_file.name)
                            if eval_match and batch_name == "batch3A":
                                # For batch3A, keep the original model string
                                original_model = eval_match.group(1)
                                original_evaluator_models.append(original_model)
                            else:
                                # For other batches, use the same as evaluator_model
                                original_evaluator_models.append(current_evaluator_model)
                    else:
                        source_files.append(None)
                        reasonings.append(None)
                        # Default evaluator model based on batch
                        if batch_name == "batch3A":
                            current_evaluator_model = "openai/gpt-4.1-mini"
                            evaluator_models.append(current_evaluator_model)
                            original_evaluator_models.append(current_evaluator_model)
                        else:
                            current_evaluator_model = "openai/gpt-4o-mini-2024-07-18"
                            evaluator_models.append(current_evaluator_model)
                            original_evaluator_models.append(current_evaluator_model)
                    
                    # Set attacker_model (default to gpt-4o-mini-2024-07-18)
                    attacker_models.append("openai/gpt-4o-mini-2024-07-18")
                
                # Add the columns to the DataFrame
                df['source_file'] = source_files
                df['attacker_model'] = attacker_models
                df['evaluator_model'] = evaluator_models
                df['original_evaluator_model'] = original_evaluator_models
                df['reasoning'] = reasonings
                
                # Ensure the DataFrame has the required columns
                # Based on enhanced_master_data.csv structure
                required_columns = [
                    "jailbreak_tactic", "test_case", "turn_type", "target_model",
                    "target_temp", "max_round", "goal_achieved", "scores", 
                    "refused", "timestamp", "batch", "source_file", "attacker_model", 
                    "evaluator_model", "original_evaluator_model", "reasoning"
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
        
        # Save the master CSV to all required directories
        master_csv_path = csv_results_dir / "master_results.csv"
        master_df.to_csv(master_csv_path, index=False)
        
        # Save to interactive_analysis/public
        interactive_path = interactive_analysis_dir / "master_results.csv"
        master_df.to_csv(interactive_path, index=False)
        
        # Save to evaluator_analysis/public
        evaluator_path = evaluator_analysis_dir / "master_results.csv"
        master_df.to_csv(evaluator_path, index=False)
        
        print(f"Created master CSV file and saved to:")
        print(f"- {master_csv_path}")
        print(f"- {interactive_path}")
        print(f"- {evaluator_path}")
        print(f"Total rows: {len(master_df)}")
    else:
        print("No data to combine. Check for errors above.")

if __name__ == "__main__":
    main() 