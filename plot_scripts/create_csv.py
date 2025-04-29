"""
Jailbreak Attack Results CSV Generator

This script converts raw jailbreak attack result files into CSV format for easier analysis
and visualization. It processes JSONL result files from attack runs and transforms them
into a structured tabular format with consistent columns and data types.

Key features:
- Processing of JSONL result files from jailbreak attack runs
- Extraction of key metrics and metadata into standardized columns
- Standardization of model names and test case identifiers
- Handling of various result file formats and structures
- Aggregation of results by various dimensions (model, tactic, test case)
- Export to CSV format for compatibility with analysis tools

This utility forms an important bridge between the raw result files produced by attack
runs and the analysis tools that require structured data. The CSV format enables easier
integration with data analysis frameworks, spreadsheet applications, and visualization tools.

Usage:
    python create_csv.py --results-dir DIRECTORY --csv OUTPUT_FILE [options]

The generated CSV serves as the input for many of the analysis and visualization
scripts in the framework.
"""

from pathlib import Path
from datetime import datetime
import argparse
import json
import re
import pandas as pd


def get_results(filepath: Path) -> tuple:
    with open(filepath, "r") as file:
        data = file.read()

    lines = data.strip().split("\n")
    data = [json.loads(line) for line in lines]

    # Get the timestamp from data or from filename
    if "timestamp" in data[0]:
        timestamp_str = data[0]["timestamp"]
    else:
        timestamp_str = "_".join(filepath.stem.split("_")[-2:])
        pattern = r"\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}"
        if not re.match(pattern, timestamp_str):
            # If the format is wrong, use the fallback timestamp
            timestamp_str = '2025-01-22_06:20:52'
            
    formats = [
        "%Y-%m-%d_%H:%M:%S",  # Format with hyphens and colons
        "%Y_%m_%d_%H_%M_%S"   # Format with all underscores
    ]
    for format_str in formats:
        try:
            timestamp = datetime.strptime(timestamp_str, format_str)
        except ValueError:
            continue

    # Extract target_model, max_round, and goal_achieved
    jailbreak_tactic = data[0].get("jailbreak_tactic")
    test_case = data[0].get("test_case")
    turn_type = data[0].get("turn_type")
    target_model = data[0].get("target_model")
    if target_model == "gpt-4o-mini":
        # add the gpt-4o-mini version for the old results
        target_model = "gpt-4o-mini-2024-07-18"
    target_temp = data[0].get("target_temp")
    max_round = max(
        (entry.get("round", 0) for entry in data if "round" in entry), default=0
    )
    goal_achieved = any(entry.get("goal_achieved", False) for entry in data)
    scores = []
    refused = 0
    for entry in data:
        if "score" in entry:
            score = entry.get("score")
            if score != "refused":
                # check if score is a float between 0 and 1
                if isinstance(score, float) and 0 <= score <= 1:
                    scores.append(score)
                else:
                    print(f"{filepath}: score is not a float between 0 and 1: {score}")
                    # raise ValueError(f"Score is not a float between 0 and 1: {score}")
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


# Get all the jsonl filenames from the given results directory and its subdirectories.
def get_jsonl_filenames(results_dir: Path) -> list:
    return [f for f in results_dir.glob('**/*.jsonl') if f.name != 'summary.jsonl']


def get_csv_results(results_dir: Path, csv_filename: Path) -> None:
    filenames = get_jsonl_filenames(results_dir)
    results = []
    for filename in filenames:
        results.append(get_results(filename))
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

    df.to_csv(csv_filename)


def main():
    parent_path = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Generate CSV file with given results data")

    parser.add_argument(
        "--results-dir",
        type=Path,
        default=parent_path / "results",
        help="Directory containing the JSONL result files to analyze (default: ../results)",
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default="results.csv",
        help="Name of the generated CSV file containing results data that will be stored under ../csv_results (default: results.csv)"
    )

    args = parser.parse_args()

    results_dir = args.results_dir
    csv_filename = parent_path/"csv_results"/args.csv

    print(f"Creating CSV file {csv_filename.name}")
    get_csv_results(results_dir, csv_filename)
    print("Done!")


if __name__ == "__main__":
    main()
