import os
import json
import glob

# Set the directory containing the .jsonl result files.
directory = '../results'  # Update this to your actual directory

summary = []

# Iterate over all .jsonl files in the directory.
for filepath in glob.glob(os.path.join(directory, '**/*.jsonl')):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Skip files that do not have enough lines (at least 3 lines: config, criteria, round data)
    if len(lines) < 3:
        continue

    try:
        # First line contains the configuration information.
        config = json.loads(lines[0])
    except Exception as e:
        print(f"Error parsing first line in {filepath}: {e}")
        continue

    # Check if the last line contains the goal_achieved indicator.
    try:
        last_obj = json.loads(lines[-1])
        if 'goal_achieved' in last_obj:
            goal_achieved = last_obj.get('goal_achieved', False)
            rounds_lines = lines[2:-1]  # Exclude criteria (second line) and the final goal indicator.
        else:
            goal_achieved = None
            rounds_lines = lines[2:]
    except Exception as e:
        goal_achieved = None
        rounds_lines = lines[2:]

    # Initialize variables for minimum score and its round.
    min_score = None
    min_round = None
    numeric_scores = []  # To collect all numeric scores for later checking.

    # Loop over the round data (starting at the third line)
    for line in rounds_lines:
        try:
            data = json.loads(line)
        except Exception as e:
            continue

        if 'score' in data:
            try:
                score = float(data['score'])
                numeric_scores.append(score)
            except (ValueError, TypeError):
                continue  # Skip non-numeric scores

            # Update if this score is lower than the current minimum.
            if min_score is None or score < min_score:
                min_score = score
                # Extract the round at which this min_score was achieved.
                min_round = data.get('round')

    # For multi-turn attacks, if all numeric scores are 10, flag no improvement.
    if config.get("turn_type") == "multi" and numeric_scores and all(s == 10 for s in numeric_scores):
        min_round = "No Improvement"

    # Add the computed fields to the config.
    config['min_score'] = min_score
    config['min_round'] = min_round
    config['goal_achieved'] = goal_achieved
    # Optionally, add the filename for reference.
    config['filename'] = os.path.basename(filepath)

    summary.append(config)

# Write the summary to a new jsonl file.
summary_file = os.path.join(directory, 'summary.jsonl')
with open(summary_file, 'w', encoding='utf-8') as out_f:
    for entry in summary:
        out_f.write(json.dumps(entry) + "\n")

print(f"Summary file created: {summary_file}")
