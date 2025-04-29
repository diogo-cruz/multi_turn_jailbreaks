# Robust Evaluation Solution

This directory contains a robust solution for evaluating AI responses with different evaluator models, handling various response formats.

## Problem

The original `evaluate_with_strongreject.py` function uses a regex pattern (`{i+1}.b \d`) to parse evaluator responses, but different evaluator models may format their responses differently. For example, some models might respond with:

```
1. 1
2. 2
3. 1
```

instead of the expected format:

```
1.b 1
2.b 2
3.b 1
```

This causes the original function to fail with a "list index out of range" error when trying to parse these responses.

## Solution

### 1. Robust Evaluation Scripts

Two versions of the solution are provided:

#### Sequential Version
- `robust_evaluation.py`: Processes files sequentially
- `run_robust_evaluation.sh`: Shell script wrapper for the sequential version

#### Parallel Version (Recommended)
- `robust_evaluation_parallel.py`: Processes files in parallel using ThreadPoolExecutor
- `run_robust_evaluation_parallel.sh`: Shell script wrapper for the parallel version

Both solutions provide:
- Multiple regex patterns to handle different response formats
- Fallback values if patterns can't be matched
- Error handling to prevent crashes
- Preservation of the original scoring logic

## Usage

### Parallel Version (Recommended)

```bash
./run_robust_evaluation_parallel.sh --results-folder <folder> [options]

# Options:
#   --evaluator-models MODEL1,MODEL2,...   Comma-separated list of evaluator models
#   --evaluator-base-url URL               Base URL for the evaluator API
#   --evaluator-temp TEMP                  Temperature for evaluation
#   --max-workers N                        Number of parallel threads (default: 16)
#   --force                                Force overwrite of existing files
#   --verbose                              Enable verbose output
#   --debug                                Debug mode (sequential with verbose output)
```

#### Examples:

Evaluate with a single model:
```bash
./run_robust_evaluation_parallel.sh --results-folder clean_results/final_runs/batch3A/crowding
```

Evaluate with multiple models:
```bash
./run_robust_evaluation_parallel.sh --results-folder clean_results/final_runs --evaluator-models openai/gpt-4.1-nano,openai/gpt-4o --max-workers 32
```

### Sequential Version

#### Running the Python Script Directly

```bash
python robust_evaluation.py <file_or_directory> [options]

# Options:
#   --evaluator-base-url URL     Base URL for the evaluator API (default: https://openrouter.ai/api/v1)
#   --evaluator-model MODEL      Model to use for evaluation (default: openai/gpt-4.1-nano)
#   --evaluator-temp TEMP        Temperature for the evaluator (default: 0.0)
#   --verbose                    Enable verbose output
#   --force                      Force overwrite of existing files
#   --api-key KEY                API key (default: use from environment)
```

#### Using the Shell Script

```bash
./run_robust_evaluation.sh [options] <directory>

# Options:
#   -m, --model MODEL   Evaluator model to use (default: openai/gpt-4.1-nano)
#   -f, --force         Force overwrite of existing files
#   -v, --verbose       Enable verbose output
#   -h, --help          Show help message
```

## Parallel Processing Performance

The parallel version utilizes ThreadPoolExecutor to process multiple files concurrently, significantly improving performance when evaluating large sets of files. The default thread count is 16, but this can be adjusted with the `--max-workers` option based on your system's capabilities.

Key features of the parallel implementation:
- Progress bar showing completion status
- Automatic logging to the `parallel_logs` directory
- Support for multiple evaluator models in a single command
- Error handling that prevents a single file failure from stopping the entire process

## Notes

- The solution keeps the original `evaluate_with_strongreject.py` file intact
- The scoring logic is the same as the original implementation
- If parsing fails completely, the script defaults to a score of 0.0 (complete refusal) 