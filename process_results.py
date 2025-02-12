from pathlib import Path
from datetime import datetime
import json
import pandas as pd

# Constants
METADATA = ["jailbreak_tactic", "test_case", "turn_type", "target_model", "target_temp"]
MODELS = [
    "gpt-4o-mini-2024-07-18",
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3.1-405b-instruct",
    "meta-llama/llama-3.2-1b-instruct",
    "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
]

def get_results(filepath: Path) -> tuple:
    # Get the timestamp from the filename
    filename = filepath.stem
    if filename.endswith("_analysis"):
        filename = filename[:-9]  # Remove _analysis suffix
    
    # Find the last set of numbers that could be a timestamp
    parts = filename.split("_")
    timestamp_parts = []
    for i in range(len(parts)-1, -1, -1):
        if parts[i].isdigit():
            timestamp_parts.insert(0, parts[i])
            if len(timestamp_parts) == 6:  # We have YYYY MM DD HH MM SS
                break
    
    if len(timestamp_parts) == 6:
        try:
            # First try with formatted timestamp (2025-02-05 01:00:00)
            year, month, day, hour, minute, second = timestamp_parts
            timestamp_str = f"{year}-{month}-{day} {hour}:{minute}:{second}"
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Then try with underscore format
                timestamp_str = "_".join(timestamp_parts)
                timestamp = datetime.strptime(timestamp_str, "%Y_%m_%d_%H_%M_%S")
            except ValueError:
                timestamp = datetime.now()
    else:
        timestamp = datetime.now()

    # Read and parse the file based on extension
    if filepath.suffix == '.jsonl':
        with open(filepath, "r") as file:
            data = file.read()
            lines = data.strip().split("\n")
            data = [json.loads(line) for line in lines]
    elif filepath.suffix == '.md':
        # For MD files, we need to extract the metadata from the filename
        parts = filepath.stem.split("_")
        data = [{
            "jailbreak_tactic": parts[0],
            "test_case": "_".join(parts[1:-7]),  # Everything between tactic and timestamp
            "turn_type": parts[-7],  # Assuming format is consistent
            "target_model": None,  # Not available in MD files
            "target_temp": None,  # Not available in MD files
            "round": 0,
            "goal_achieved": False  # Would need to parse MD content to determine this
        }]
    else:
        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    # Extract metadata and results
    jailbreak_tactic = data[0].get("jailbreak_tactic")
    test_case = data[0].get("test_case")
    turn_type = data[0].get("turn_type")
    target_model = data[0].get("target_model")
    target_temp = data[0].get("target_temp")
    max_round = max(
        (entry.get("round", 0) for entry in data if "round" in entry), default=0
    )
    goal_achieved = any(entry.get("goal_achieved", False) for entry in data)
    scores = []
    refused = 0
    
    if filepath.suffix == '.jsonl':
        for i in range(2, len(data) - 1):
            score = data[i].get("score")
            if score != "refused":
                if isinstance(score, int):
                    scores.append(score)
                else:
                    raise ValueError(f"Score is not an integer: {score}")
            else:
                refused += 1

    return (
        jailbreak_tactic,
        test_case,
        turn_type,
        target_model,
        target_temp,
        max_round,
        goal_achieved,
        scores,
        refused,
        timestamp,
    )

def get_result_filenames(results_dir: Path) -> list:
    """Get both JSONL and MD files"""
    return [f for f in results_dir.iterdir() if f.suffix in ['.jsonl', '.md']]

def get_filenames_for_key(results_dir: Path, key: str) -> list:
    filenames = get_result_filenames(results_dir)
    return [f for f in filenames if key in f.name]

def get_results_for_key(results_dir: Path, key: str) -> pd.DataFrame:
    filenames = get_filenames_for_key(results_dir, key)
    results = []
    for filename in filenames:
        try:
            results.append(get_results(filename))
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    df = pd.DataFrame(
        results,
        columns=[
            "jailbreak_tactic",
            "test_case",
            "turn_type",
            "target_model",
            "target_temp",
            "max_round",
            "goal_achieved",
            "scores",
            "refused",
            "timestamp",
        ],
    )
    return df 