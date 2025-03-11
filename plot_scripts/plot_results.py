from pathlib import Path
from datetime import datetime
import argparse
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons

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
    timestamp_str = "_".join(filepath.stem.split("_")[-2:])
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H:%M:%S")
    except ValueError:
        # If the format is wrong, use the fallback timestamp
        timestamp = datetime.strptime('2025-01-22_06:20:52', "%Y-%m-%d_%H:%M:%S")
    
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
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H:%M:%S")

    # Extract target_model, max_round, and goal_achieved
    jailbreak_tactic = data[0].get("jailbreak_tactic")
    test_case = data[0].get("test_case")
    turn_type = data[0].get("turn_type")
    target_model = data[0].get("target_model")
    # target_temp = data[0].get("target_temp")
    target_temp = 0.0
    max_round = max(
        (entry.get("round", 0) for entry in data if "round" in entry), default=0
    )
    goal_achieved = any(entry.get("goal_achieved", False) for entry in data)
    scores = []
    refused = 0
    for i in range(2, len(data) - 1):
        score = data[i].get("score")
        if score != "refused":
            # check if score is an integer
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


# Get all the jsonl filenames from the given results directory.
def get_jsonl_filenames(results_dir: Path) -> list:
    return [f for f in results_dir.iterdir() if f.suffix == ".jsonl"]


def get_filenames_for_key(results_dir: Path, keys: list[str]) -> list:
    filenames = get_jsonl_filenames(results_dir)
    result = []
    if len(keys) == 1:
        return [f for f in filenames if key in f.name]
    else :
        # if multiple keys were submitted, use first one as a required key 
        # A file should have at least one of the remaining key to be included in the filtered list 
        for key in keys[1:]:
            result += [f for f in filenames if key in f.name and keys[0] in f.name]
        return result


def get_results_for_key(results_dir: Path, key: str) -> pd.DataFrame:
    filenames = get_filenames_for_key(results_dir, key)
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
    return df


# Check that the dataframe has the given columns
def check_columns(df: pd.DataFrame, given_columns: list) -> None:
    for column in given_columns:
        if column not in df.columns:
            raise ValueError(f"Dataframe does not have column {column}")


def add_run_column(df: pd.DataFrame, given_columns: list) -> pd.DataFrame:
    # First check that the dataframe has the given columns and timestamp
    check_columns(df, given_columns + ["timestamp"])

    # Sort by timestamp for each group of given_columns
    df = df.sort_values(given_columns + ["timestamp"])

    # Group by given_columns and assign run numbers
    df["run"] = df.groupby(given_columns).cumcount() + 1

    return df


# Get the most recent results for each group of METADATA values
def get_most_recent_results(df: pd.DataFrame) -> pd.DataFrame:
    # First check that the dataframe has the columns of METADATA
    check_columns(df, METADATA + ["timestamp"])

    if df.empty:
        return pd.DataFrame(columns=df.columns)

    # Group by METADATA to locate the most recent timestamp
    # Fix for deprecation warning by explicitly selecting non-grouping columns
    latest_indices = df.groupby(METADATA)["timestamp"].idxmax()
    return df.loc[latest_indices].reset_index(drop=True)


# Get the groups of METADATA values with multiple results
def get_multiple_results(df: pd.DataFrame) -> pd.DataFrame:
    # First check that the dataframe has the columns of METADATA
    check_columns(df, METADATA)

    return df.groupby(METADATA).filter(lambda x: len(x) > 1).reset_index(drop=True)


def prepare_model_plot(df: pd.DataFrame) -> tuple:
    # First check that the dataframe has the columns METADATA + ['scores']
    check_columns(df, METADATA + ["scores"])

    # Handle empty DataFrame
    if df.empty:
        raise ValueError("DataFrame is empty - no data to plot")

    # Check that the dataframe has unique values for turn_type and target_temp
    if len(df["turn_type"].unique()) > 1 or len(df["target_temp"].unique()) > 1:
        raise ValueError("Dataframe has multiple values for turn_type or target_temp")

    turn_type = df["turn_type"].iloc[0]
    target_temp = df["target_temp"].iloc[0]

    return turn_type, target_temp


def create_interactive_grid_plot_with_label_model(df: pd.DataFrame) -> None:
    turn_type, target_temp = prepare_model_plot(df)

    # Get unique values for grid dimensions and labels
    test_cases = df["test_case"].unique()
    tactics = df["jailbreak_tactic"].unique()
    models = df["target_model"].unique()

    # Create figure and grid of subplots
    fig, axes = plt.subplots(
        len(tactics), len(test_cases), figsize=(4 * len(test_cases), 3 * len(tactics))
    )
    plt.subplots_adjust(
        left=0.2, right=0.85, bottom=0.1, top=0.9, wspace=0.3, hspace=0.4
    )

    # Dictionary to store line objects for each model
    lines_dict = {model: [] for model in models}

    # Create plots for each combination
    for i, tactic in enumerate(tactics):
        for j, test in enumerate(test_cases):
            if len(tactics) == 1 and len(test_cases) == 1:
                ax = axes
            else:
                ax = axes[i, j] if len(tactics) > 1 else axes[j]
            
            # Set title for each subplot
            ax.set_title(f"Using {tactic} on {test}", fontsize="small", pad=10)

            # Add axis labels
            ax.set_xlabel("Round")
            ax.set_ylabel("Score")

            # Get data for this subplot
            mask = (df["jailbreak_tactic"] == tactic) & (df["test_case"] == test)
            subplot_data = df[mask]

            # Plot each model's scores
            for model in models:
                model_data = subplot_data[subplot_data["target_model"] == model]
                if not model_data.empty:
                    scores = model_data.iloc[0]["scores"]
                    rounds = range(1, len(scores) + 1)
                    (line,) = ax.plot(rounds, scores, label=model)
                    lines_dict[model].append(line)

            ax.set_ylim(0.5, 10.5)  # Scores range from 1 to 10
            ax.grid(True)

            # Add legend to lower right of each subplot
            ax.legend(loc="lower right", fontsize="small")

    # Create checkbuttons
    rax = plt.axes([0.87, 0.4, 0.08, 0.2])
    check = CheckButtons(rax, models, [True] * len(models))

    def func(label):
        # Toggle visibility of lines for selected model
        for line in lines_dict[label]:
            line.set_visible(not line.get_visible())
        fig.canvas.draw_idle()

    check.on_clicked(func)

    # Add title to the figure
    fig.suptitle(f"{turn_type} turn with temperature {target_temp}", fontsize="large")

    plt.tight_layout()
    plt.show()


def create_box_grid_plot_with_model(df: pd.DataFrame) -> None:
    turn_type, target_temp = prepare_model_plot(df)

    # Get unique values for grid dimensions
    test_cases = df["test_case"].unique()
    jailbreak_tactics = df["jailbreak_tactic"].unique()
    n_rows = len(jailbreak_tactics)
    n_cols = len(test_cases)

    # Create figure and axes grid
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    fig.tight_layout(pad=5)

    # If there's only one row or column, wrap axes in a 2D array for consistent indexing
    if n_rows == 1:
        axs = axs.reshape(1, -1)
    if n_cols == 1:
        axs = axs.reshape(-1, 1)

    # Iterate through each combination of jailbreak_tactic and test_case
    for i, tactic in enumerate(jailbreak_tactics):
        for j, test in enumerate(test_cases):
            # Filter data for current subplot
            mask = (df["jailbreak_tactic"] == tactic) & (df["test_case"] == test)
            subplot_data = df[mask]

            # Prepare data for box plot
            box_data = []
            labels = []
            for model in df["target_model"].unique():
                model_scores = subplot_data[subplot_data["target_model"] == model]["scores"].tolist()[0]
                if model_scores:  # Only add if there's data
                    box_data.append(model_scores)
                    labels.append(model)

            # Create box plot
            if box_data:  # Only create plot if there's data
                axs[i, j].boxplot(box_data, tick_labels=labels)

                # Customize subplot
                axs[i, j].set_title(f"{tactic} on {test}")
                axs[i, j].set_ylabel("Score")
                axs[i, j].grid(True)

                # Rotate x-axis labels
                axs[i, j].tick_params(axis="x", rotation=45)

                # Ensure y-axis shows full score range
                axs[i, j].set_ylim(0.5, 10.5)

    # Add title to the figure
    fig.suptitle(f"{turn_type} turn with temperature {target_temp}", fontsize="large")
    plt.subplots_adjust(top=0.9)
    # Display the plot
    plt.show()


def prepare_run_plot(df: pd.DataFrame) -> tuple:
    # Add run column to the dataframe
    df = add_run_column(df, METADATA)

    # Check that the dataframe has the column scores
    check_columns(df, ["scores"])

    # Handle empty DataFrame
    if df.empty:
        raise ValueError("DataFrame is empty - no data to plot")

    # Check that the dataframe has unique values for jailbreak_tactic, test_case, turn_type and target_temp
    if (
        len(df["jailbreak_tactic"].unique()) > 1
        or len(df["test_case"].unique()) > 1
        or len(df["turn_type"].unique()) > 1
        or len(df["target_temp"].unique()) > 1
    ):
        raise ValueError(
            "Dataframe has multiple values for jailbreak_tactic, test_case, turn_type or target_temp"
        )

    jailbreak_tactic = df["jailbreak_tactic"].iloc[0]
    test_case = df["test_case"].iloc[0]
    turn_type = df["turn_type"].iloc[0]
    target_temp = df["target_temp"].iloc[0]

    return df, jailbreak_tactic, test_case, turn_type, target_temp


def create_interactive_grid_plot_with_label_run(df: pd.DataFrame) -> None:
    df, jailbreak_tactic, test_case, turn_type, target_temp = prepare_run_plot(df)

    # Get unique target models
    target_models = df["target_model"].unique()
    n_models = len(target_models)

    # Create figure and axes grid
    fig, axes = plt.subplots(n_models, 1, figsize=(10, 4 * n_models))
    if n_models == 1:
        axes = [axes]

    # Dictionary to store line objects for each subplot
    lines_dict = {}

    # Create plots for each target model
    for idx, (target_model, ax) in enumerate(zip(target_models, axes)):
        model_data = df[df["target_model"] == target_model]

        # Store lines for this subplot
        lines_dict[target_model] = []

        # Plot each run
        for run_num in model_data["run"].unique():
            run_data = model_data[model_data["run"] == run_num]
            scores = run_data["scores"].iloc[0]  # Get the scores list
            rounds = range(1, len(scores) + 1)

            (line,) = ax.plot(rounds, scores, label=f"Run {run_num}")
            lines_dict[target_model].append(line)

        # Customize subplot
        ax.set_title(target_model)
        ax.set_xlabel("Round")
        ax.set_ylabel("Score")
        ax.legend(loc="lower right")
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add checkbuttons for each subplot
    checkbuttons = []
    for idx, target_model in enumerate(target_models):
        # Calculate position for checkbutton
        # Place it to the right of each subplot
        ax_pos = axes[idx].get_position()
        button_ax = plt.axes([0.85, ax_pos.y0 + ax_pos.height / 2, 0.1, 0.15])

        # Create labels for the runs
        labels = [f"run {i + 1}" for i in range(len(lines_dict[target_model]))]

        # Create checkbutton
        check = CheckButtons(button_ax, labels, [True] * len(labels))

        # Create a closure that properly captures the target_model
        def make_callback(target_model):
            def callback(label):
                run_idx = int(label.split()[-1]) - 1
                lines_dict[target_model][run_idx].set_visible(
                    not lines_dict[target_model][run_idx].get_visible()
                )
                plt.draw()

            return callback

        # Attach the callback
        check.on_clicked(make_callback(target_model))
        checkbuttons.append(check)

    # Add title to the figure
    fig.suptitle(
        f"{jailbreak_tactic} on {test_case} \nwith {turn_type} turn and temperature {target_temp}",
        fontsize="large",
    )
    # Adjust layout to prevent overlap
    plt.subplots_adjust(top=0.8, right=0.8)
    plt.tight_layout()
    plt.show()


def create_box_grid_plot_with_run(df: pd.DataFrame) -> None:
    df, jailbreak_tactic, test_case, turn_type, target_temp = prepare_run_plot(df)

    # Get unique target models
    target_models = df["target_model"].unique()
    n_models = len(target_models)

    # Create figure and axes
    fig, axes = plt.subplots(n_models, 1, figsize=(10, 4 * n_models))
    if n_models == 1:
        axes = [axes]

    # Create box plot for each target model
    for idx, (ax, model) in enumerate(zip(axes, target_models)):
        # Get data for current model
        model_data = df[df["target_model"] == model]

        # Extract scores and prepare data for box plot
        plot_data = [scores for scores in model_data["scores"]]

        # Create box plot
        ax.boxplot(plot_data)

        # Customize plot
        ax.set_title(model)
        ax.set_ylabel("Score")

        # Set x-axis labels
        n_runs = len(model_data)
        ax.set_xticks(range(1, n_runs + 1))
        ax.set_xticklabels([f"Run {i}" for i in range(1, n_runs + 1)])

        # Set y-axis limits to show full range of scores (1-10)
        ax.set_ylim(0.5, 10.5)

        # Add grid for better readability
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add title to the figure
    fig.suptitle(
        f"{jailbreak_tactic} on {test_case} \nwith {turn_type} turn and temperature {target_temp}",
        fontsize="large",
    )
    plt.subplots_adjust(top=0.8)
    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.show()


def main():
    current_path = Path(__file__).parent

    parser = argparse.ArgumentParser(
        description="Plot and analyze model evaluation results from JSONL files."
    )

    parser.add_argument(
        "--results-dir",
        type=Path,
        default=current_path / "results",
        help="Directory containing the JSONL result files to analyze (default: ./results)",
    )

    parser.add_argument(
        "--key",
        type=str,
        nargs='*',  # zero or more arguments
        default=[],  # default to empty list
        help="Filter results files by this key in their filename (default: no filter)",
    )

    parser.add_argument(
        "--turn-type",
        type=str,
        choices=["single", "multi"],
        default="multi",
        help="Type of conversation turn to analyze: single or multi-turn interactions (default: multi)",
    )

    parser.add_argument(
        "--temp",
        type=float,
        choices=[0.0, 1.0],
        default=0.0,
        help="Temperature setting used in model evaluation: 0.0 or 1.0 (default: 0.0)",
    )

    parser.add_argument(
        "--plot-type",
        type=str,
        choices=["model", "run"],
        default="model",
        help="Type of plot to generate: 'model' for comparing different models, 'run' for comparing multiple runs of the same configuration (default: model)",
    )

    parser.add_argument(
        "--no-interactive-plot",
        action="store_false",
        dest="interactive_plot",
        help="Generate static plots instead of interactive plots with checkbuttons (default: interactive)",
    )

    parser.add_argument(
        "--goal-achieved-only",
        action="store_true",
        help="Only include results where the evaluation goal was achieved (default: include all results)",
    )

    parser.add_argument(
        "--refused-only",
        action="store_true",
        help="Only include results where the model refused at least once (default: include all results)",
    )

    args = parser.parse_args()

    df = get_results_for_key(args.results_dir, args.key)
    print(f"{len(df)} data collected.")

    if df.empty:
        print("No data found matching the specified criteria")
        return

    if args.goal_achieved_only:
        df = df[df["goal_achieved"]]
    if args.refused_only:
        df = df[df["refused"] > 0]

    mask = (df["turn_type"] == args.turn_type) & (df["target_temp"] == args.temp)
    # mask = (df["turn_type"] == args.turn_type)
    df = df[mask]
    print(f"{len(df)} data remained.")

    try:
        if args.plot_type == "model":
            # df = get_most_recent_results(df)
            print(f"{len(df)} data remained.")
            if df.empty:
                print("No data found after getting most recent results")
                return
            if args.interactive_plot:
                create_interactive_grid_plot_with_label_model(df)
            else:
                create_box_grid_plot_with_model(df)
        elif args.plot_type == "run":
            df = get_multiple_results(df)
            if df.empty:
                print("No data found with multiple results")
                return
            if args.interactive_plot:
                create_interactive_grid_plot_with_label_run(df)
            else:
                create_box_grid_plot_with_run(df)
    except ValueError as e:
        print(f"Error: {str(e)}")
        return


if __name__ == "__main__":
    main()
