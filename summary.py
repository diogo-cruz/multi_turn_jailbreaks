import os
import json
import glob

# Set the directory containing the .jsonl result files.
# Replace 'path_to_directory' with your actual directory.
directory = './results'

summary = []

# Iterate over all .jsonl files in the directory.
for filepath in glob.glob(os.path.join(directory, '*.jsonl')):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Skip files that do not have enough lines (at least 3 lines: config, criteria, round info)
    if len(lines) < 3:
        continue

    try:
        # First line contains all the configuration information.
        config = json.loads(lines[0])
    except Exception as e:
        print(f"Error parsing first line in {filepath}: {e}")
        continue

    # Determine if the last line is the goal_achieved indicator.
    try:
        last_obj = json.loads(lines[-1])
        if 'goal_achieved' in last_obj:
            goal_achieved = last_obj.get('goal_achieved', False)
            rounds_lines = lines[2:-1]  # from third line up until the second-to-last line
        else:
            goal_achieved = None
            rounds_lines = lines[2:]
    except Exception as e:
        goal_achieved = None
        rounds_lines = lines[2:]

    # Find the minimum numeric score from the rounds.
    min_score = None
    for line in rounds_lines:
        try:
            data = json.loads(line)
        except Exception as e:
            continue

        # Only consider entries that have a score.
        if 'score' in data:
            # Try converting the score to a float (skip if not numeric).
            try:
                score = float(data['score'])
            except (ValueError, TypeError):
                continue

            if min_score is None or score < min_score:
                min_score = score
                # Extract the round at which this min_score was achieved.
                min_round = data.get('round')

    # Combine the config with the computed fields.
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
