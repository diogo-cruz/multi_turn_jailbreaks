"""
Jailbreak Attack Response Reevaluation Framework

This script provides functionality for reevaluating existing jailbreak attack results
using different evaluation criteria or models. It allows researchers to apply updated
or alternative evaluation methodologies to previously collected attack data without
needing to rerun the actual attacks.

Key features:
- Loading and parsing of existing attack result files
- Extraction of target model responses for reevaluation
- Application of various evaluation methodologies to assess attack success
- Support for different evaluator models with configurable parameters
- Preservation of original attack data alongside new evaluation results
- Detailed logging of reevaluation process and outcomes

This framework is particularly useful when new evaluation methods are developed
or when comparing different methods of determining jailbreak success. It enables
more consistent comparisons across experiments by allowing retroactive application
of standardized evaluation criteria.

Usage:
    python reevaluate_responses.py [options]

The script is typically invoked by the run_reevaluation_parallel.sh script for
efficient processing of large result sets.
"""

import os
import json
import argparse
import openai
import tqdm
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from utils import generate
from utils.evaluate_with_strongreject import evaluate_with_strongreject
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug print function that forces flushing
def debug_print(message):
    print(message, file=sys.stderr, flush=True)

def evaluator_generate(messages, client, model, temperature=0.0, **kwargs):
    # Remove temperature from kwargs if it's already provided as an argument
    if 'temperature' in kwargs:
        del kwargs['temperature']
    return generate(messages, client=client, model=model, temperature=temperature, **kwargs)

def reevaluate_file(file_path, evaluator_client, evaluator_model, evaluator_temp, dry_run=False):
    try:
        # Read the original file
        with open(file_path, 'r') as f:
            lines = f.read().strip().split('\n')
        
        if not lines:
            debug_print(f"Empty file: {file_path}")
            return
            
        # Parse the metadata from the first line
        metadata = json.loads(lines[0])
        
        # Create the new file path with evaluator model name
        dir_path = os.path.dirname(file_path)
        base_filename = os.path.basename(file_path)
        model_name = evaluator_model.split('/')[-1]
        new_file_path = os.path.join(dir_path, f"{os.path.splitext(base_filename)[0]}_eval_{model_name}.jsonl")
        
        # Skip if file already exists
        if os.path.exists(new_file_path):
            return new_file_path
            
        if dry_run:
            debug_print(f"Would process: {file_path} -> {new_file_path}")
            return new_file_path

        # Debug information
        debug_print(f"\n========================")
        debug_print(f"Processing: {os.path.basename(file_path)}")
        debug_print(f"========================")
        
        # Write the metadata to the new file
        with open(new_file_path, 'w') as f:
            # Update metadata with new evaluator info
            metadata["original_evaluator_model"] = metadata.get("evaluator_model", "unknown")
            metadata["evaluator_model"] = evaluator_model
            metadata["evaluator_temp"] = evaluator_temp
            f.write(json.dumps(metadata) + '\n')
        
        # Process each round
        rounds_data = []
        for i in range(1, len(lines)):
            line = lines[i]
            
            # Skip goal_achieved line or any non-round data
            if '"round":' not in line:
                continue
                
            data = json.loads(line)
            if "round" in data and "assistant" in data:
                rounds_data.append(data)
        
        debug_print(f"  Found {len(rounds_data)} rounds to evaluate")
        
        # Define evaluator function for this file
        def eval_generate(messages, **kwargs):
            # Make sure we don't pass temperature twice
            if 'temperature' in kwargs:
                del kwargs['temperature']
            return generate(messages, client=evaluator_client, 
                           model=evaluator_model, temperature=evaluator_temp, **kwargs)
        
        # Re-evaluate each round
        goal = metadata.get("task", "Unknown task")
        
        for idx, data in enumerate(rounds_data):
            round_num = data["round"]
            user_prompt = data["user"]
            response = data["assistant"]
            
            debug_print(f"  Evaluating round {round_num}...")
            # Print the first 50 chars of the response
            response_preview = response[:50] + "..." if len(response) > 50 else response
            debug_print(f"    Response preview: {response_preview}")
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
            
            # Re-evaluate the response
            try:
                debug_print(f"    Starting evaluation with {evaluator_model}...")
                new_score = evaluate_with_strongreject(response, goal, eval_generate)
                debug_print(f"    Score: {new_score}")
            except Exception as e:
                debug_print(f"    Error in evaluation: {str(e)}")
                # If there's an error, try to use the original score if available
                new_score = data.get("score", 0)
                debug_print(f"    Using original score: {new_score}")
            
            # Write the updated round data
            with open(new_file_path, 'a') as f:
                output_data = {
                    "round": round_num,
                    "user": user_prompt,
                    "assistant": response,
                    "score": new_score
                }
                f.write(json.dumps(output_data) + '\n')
                debug_print(f"    Wrote round {round_num} data to file")
        
        # Check if goal was achieved in any round
        goal_achieved = any(round_data.get("score", 0) == 1 for round_data in rounds_data)
        
        # Add any remaining lines (like goal_achieved status)
        with open(new_file_path, 'a') as f:
            f.write(json.dumps({"goal_achieved": goal_achieved}) + '\n')
            debug_print(f"    Wrote goal_achieved: {goal_achieved}")
        
        debug_print(f"  Completed processing: {os.path.basename(new_file_path)}")
        with open(new_file_path, 'r') as f:
            line_count = len(f.readlines())
            debug_print(f"  Final file has {line_count} lines (expected {len(rounds_data) + 2})")
            
        return new_file_path
            
    except Exception as e:
        debug_print(f"Error processing {file_path}: {str(e)}")
        import traceback
        debug_print(traceback.format_exc())
        return None

def process_directory(directory, evaluator_client, evaluator_model, evaluator_temp, 
                     max_workers=16, dry_run=False, verbose=False):
    tasks = []
    
    # Check directory structure
    tactic_folders = []
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            tactic_folders.append(item)
            
    if tactic_folders:
        debug_print(f"Found tactic subfolders in {directory}: {', '.join(tactic_folders)}")
    
    # Walk through all subdirectories
    for root, _, files in os.walk(directory):
        # Specifically filter to only include original files (without _eval_ in the name)
        original_jsonl_files = [f for f in files if f.endswith('.jsonl') and '_eval_' not in f]
        
        if original_jsonl_files and verbose:
            rel_path = os.path.relpath(root, directory)
            if rel_path == '.':
                debug_print(f"Found {len(original_jsonl_files)} original JSONL files in root directory")
            else:
                debug_print(f"Found {len(original_jsonl_files)} original JSONL files in {rel_path}/")
                
        for filename in original_jsonl_files:
            file_path = os.path.join(root, filename)
            tasks.append(file_path)
    
    debug_print(f"Found {len(tasks)} total original files to process")
    
    if dry_run:
        debug_print("Dry run mode: no files will be modified")
        # Just show the first few files that would be processed
        for file_path in tasks[:5]:
            reevaluate_file(file_path, evaluator_client, evaluator_model, evaluator_temp, dry_run=True)
        if len(tasks) > 5:
            debug_print(f"... and {len(tasks) - 5} more files")
        return []
    
    # For debugging: process only a few files sequentially
    if verbose and max_workers == 1:
        debug_print("Processing in debug mode (sequential, with verbose output)...")
        # Process only 1 file for debugging
        debug_sample = tasks[:1] if len(tasks) > 0 else tasks
        debug_print(f"Selected file for debug: {os.path.basename(debug_sample[0])}")
        results = []
        for file_path in debug_sample:
            result = reevaluate_file(file_path, evaluator_client, evaluator_model, evaluator_temp)
            results.append(result)
        successful = [r for r in results if r is not None]
        debug_print(f"Successfully processed {len(successful)}/{len(debug_sample)} files")
        return successful
    
    # Process files in parallel
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Use tqdm for a progress bar
        for result in tqdm.tqdm(
            executor.map(
                lambda f: reevaluate_file(f, evaluator_client, evaluator_model, evaluator_temp), 
                tasks
            ), 
            total=len(tasks),
            desc=f"Reevaluating with {evaluator_model}"
        ):
            results.append(result)
    
    successful = [r for r in results if r is not None]
    debug_print(f"Successfully processed {len(successful)}/{len(tasks)} files")
    return successful

def main():
    parser = argparse.ArgumentParser(description="Re-evaluate existing runs with a different evaluator model")
    parser.add_argument(
        "--evaluator-base-url", 
        type=str, 
        help="The evaluator model's base URL for the OpenAI API", 
        default="https://openrouter.ai/api/v1",
    )
    parser.add_argument(
        "--evaluator-model", 
        type=str, 
        help="The evaluator model name", 
        default="openai/gpt-4o",
    )
    parser.add_argument(
        "--evaluator-temp", 
        type=float, 
        help="The temperature to use for the evaluator model", 
        default=0.0,
    )
    parser.add_argument(
        "--results-folder",
        type=str,
        help="The folder containing results to re-evaluate",
        required=True,
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers",
        default=16,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't actually modify files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for the evaluator model (default: uses key from .env file)",
        default=None,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode - process files sequentially with verbose output",
    )
    
    args = parser.parse_args()
    
    debug_print("Starting script with args:")
    debug_print(str(args))
    
    # Verify the results folder exists
    if not os.path.exists(args.results_folder):
        debug_print(f"Error: Results folder '{args.results_folder}' does not exist")
        return
        
    if not os.path.isdir(args.results_folder):
        debug_print(f"Error: '{args.results_folder}' is not a directory")
        return
    
    # Get API key from arguments or environment variables
    api_key = args.api_key
    if api_key is None:
        # Try to get from environment variables (loaded from .env file)
        if "openrouter.ai" in args.evaluator_base_url:
            api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            
    if not api_key:
        debug_print("Error: API key not found. Please check your .env file contains OPENAI_API_KEY or OPENROUTER_API_KEY.")
        return
    else:
        debug_print("API key found")
    
    # Initialize the evaluator client
    evaluator_client = openai.OpenAI(
        base_url=args.evaluator_base_url,
        api_key=api_key
    )
    
    # Run the reevaluation
    debug_print(f"Re-evaluating results in {args.results_folder} with model {args.evaluator_model}")
    
    # Override max_workers for debug mode
    max_workers = 1 if args.debug else args.max_workers
    
    process_directory(
        args.results_folder, 
        evaluator_client, 
        args.evaluator_model, 
        args.evaluator_temp,
        max_workers,
        args.dry_run,
        args.verbose or args.debug
    )
    
    debug_print("Reevaluation completed!")

if __name__ == "__main__":
    # Force immediate output
    sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1)
    sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)
    debug_print("Script starting...")
    main() 