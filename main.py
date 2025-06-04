"""
Multi-Turn Jailbreak Attack Framework

This script serves as the main entry point for executing automated jailbreak attacks against 
target language models. It orchestrates the process of loading test cases, configuring models,
and executing various jailbreak tactics in either single-turn or multi-turn conversation modes.

The framework supports:
- Multiple jailbreak tactics (crescendomation, actor_attack, opposite_day, etc.)
- Configuration of both target and attacker models with custom temperature settings
- Parallel execution of multiple samples of the same test configuration
- Comprehensive logging of attack results for analysis

Usage:
    python main.py --jailbreak-tactic TACTIC --test-case CASE --target-model MODEL [options]

See README.md for detailed documentation on the framework and supported tactics.
"""

import os
import datetime
import argparse
import openai
import json
import importlib
import asyncio
from dotenv import load_dotenv
from utils import generate, run, generate_score_rubric
from utils.generate import (
    NO_REASONING_SUPPORTED_MODELS, 
    ALWAYS_REASONING_MODELS, 
    THINKING_VARIANTS,
    QWEN_MODELS
)


# Load the API keys from the .env file
load_dotenv()

# Get available jailbreak tactics
JAILBREAK_TACTICS = [d for d in os.listdir('jailbreaks') 
                    if os.path.isdir(os.path.join('jailbreaks', d))]

# Get available test cases
TEST_CASES = [d for d in os.listdir('test_cases')
              if os.path.isdir(os.path.join('test_cases', d))]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model-base-url", 
    type=str, 
    help="The model base URL for the OpenAI API", 
    default="https://openrouter.ai/api/v1",
)
parser.add_argument(
    "--target-model", 
    type=str, 
    help="The target model name", 
    default="gpt-4o",
)
parser.add_argument(
    "--target-temp", 
    type=float, 
    help="The temperature to use for the target model", 
    default=0.0,
)
parser.add_argument(
    "--attacker-model", type=str, help="The attacker model name", default="gpt-4o-mini"
)
parser.add_argument(
    "--attacker-temp", type=float, help="The temperature to use for the attacker model", default=0.0
)
parser.add_argument(
    "--evaluator-model", type=str, help="The evaluator model name", default="gpt-4o-mini"
)
parser.add_argument(
    "--evaluator-temp", type=float, help="The temperature to use for the evaluator model", default=0.0
)
parser.add_argument(
    "--test-case", 
    type=str, 
    help="Name of the test case to run", 
    choices=TEST_CASES,
    default="how_to_make_bomb",
)
parser.add_argument(
    "--turn-type",
    type=str,
    help="Specify to run the single-turn version of the test case or the multi-turn",
    choices=['single_turn', 'multi_turn'],
    default='multi_turn'    
)
parser.add_argument(
    "--jailbreak-tactic",
    type=str,
    help="The jailbreak tactic to use",
    choices=JAILBREAK_TACTICS,
    default="crescendomation",
)
parser.add_argument(
    "--output-folder",
    type=str,
    help="The folder name to save results in (under ./clean_results/final_runs/)",
    default="batch2D_2",
)
parser.add_argument(
    "--gen-score-rubric",
    action="store_true",
    help="If set, generate the score rubric",
)
parser.add_argument(
    "--gen-score-rubric-test-cases",
    nargs="*",
    default=None,
    help="List of test cases to generate rubric for (space-separated), or None for all",
)
parser.add_argument(
    "--samples",
    type=int,
    default=1,
    help="Number of parallel samples to run",
)
parser.add_argument(
    "--reasoning",
    type=str,
    default=None,
    choices=["none", "low", "medium", "high"],
    help="Reasoning mode for models. Options: none, low, medium, high. None to disable reasoning control.",
)
args = parser.parse_args()

if not run.has_single_turn(args.jailbreak_tactic) and args.turn_type == 'single_turn':
    print(f"Skipping single turn for '{args.jailbreak_tactic}', as it does not have a single-turn implementation.")
    # Exit the program
    exit(0)

target_client = openai.OpenAI(base_url=args.model_base_url)
target_model = args.target_model
target_temp = args.target_temp
reasoning = args.reasoning

def validate_model_reasoning_compatibility(model: str, reasoning: str) -> bool:
    """
    Validate if the given model supports the specified reasoning mode.

    Args:
        model (str): The model name to validate.
        reasoning (str): The reasoning mode to validate against the model.
    
    Returns:
        bool: True if the model supports the reasoning mode, False otherwise.
    """
    if reasoning == "none":
        valid_none_models = NO_REASONING_SUPPORTED_MODELS + ALWAYS_REASONING_MODELS + THINKING_VARIANTS + QWEN_MODELS
        if model not in valid_none_models:
            print(f"ERROR: Model {model} does not support 'none' reasoning mode")
            print("Valid models that support 'none' reasoning:")
            for m in sorted(valid_none_models):
                print(f"  - {m}")
            return False
    return True

def target_generate(messages, **kwargs):
    try:
        return generate(messages, client=target_client, model=target_model, temperature=target_temp, reasoning=reasoning, **kwargs)
    except ValueError as e:
        #TODO: do we still need this check since we validate reasoning compatibility above?
        print(f"ERROR: {str(e)}")
        print("Exiting due to incompatible reasoning settings with the selected model.")
        exit(1)

attacker_client = openai.OpenAI(base_url=args.model_base_url)
attacker_model = args.attacker_model
attacker_temp = args.attacker_temp

evaluator_client = openai.OpenAI(base_url=args.model_base_url)
evaluator_model = args.evaluator_model
evaluator_temp = args.evaluator_temp


def attacker_generate(messages, temperature=attacker_temp, **kwargs):
    return generate(messages, client=attacker_client, model=attacker_model, 
    temperature=temperature, **kwargs)
    
def evaluator_generate(messages, temperature=evaluator_temp, **kwargs):
    return generate(messages, client=evaluator_client, model=evaluator_model, 
    temperature=temperature, **kwargs)


# if args.gen_score_rubric:
#     test_cases_dir = "test_cases"
#     test_cases = [d for d in os.listdir(test_cases_dir) if os.path.isdir(os.path.join(test_cases_dir, d))] if args.gen_score_rubric_test_cases is None else args.gen_score_rubric_test_cases

#     for t in test_cases:
#         print(f"Generating score rubric for {t}")
#         test_case_path = os.path.join(test_cases_dir, t, "multi_turn.json")
#         with open(test_case_path, "r") as f:
#             test_case = json.load(f)
        
#         goal = test_case["task"]
#         success_condition = test_case.get("success_condition", None)
#         criteria = generate_score_rubric.generate_rubric(goal, attacker_generate, success_condition)

#         score_rubric_path = os.path.join(test_cases_dir, t, "score_rubric.json")
#         with open(score_rubric_path, "w") as file:
#             json.dump({"score_rubric": criteria}, file, indent=2)
        
# Load the appropriate test case file based on whether it's single or multi turn
test_case_file = f"{args.turn_type}.json"
test_case_path = os.path.join("test_cases", args.test_case, test_case_file)

with open(test_case_path, "r") as f:
    test_case = json.load(f)

# test_case_score_rubric_path = os.path.join("test_cases", args.test_case, "score_rubric.json")

# with open(test_case_score_rubric_path, "r") as f:
#     test_case_score_rubric = json.load(f)

current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
timestamp = {"timestamp": current_time}

target_model_name = args.target_model.split("/")[-1]

# Before running the attack, validate the model and reasoning compatibility
if (reasoning is not None) and (not validate_model_reasoning_compatibility(target_model, reasoning)):
    print("Exiting due to incompatible reasoning settings with the selected model.")
    exit(1)

# Function to run a single sample
async def run_sample(sample_num):
    # Create a unique output file path for each sample
    # Add reasoning suffix to filename if reasoning is not None
    reasoning_suffix = f"_reasoning_{reasoning}" if reasoning is not None else ""
    output_file_path = (
        f"./clean_results/final_runs/{args.output_folder}/{args.jailbreak_tactic}/{args.jailbreak_tactic}_{args.test_case}_{target_model_name}_{args.turn_type}{reasoning_suffix}_sample{sample_num}_{current_time}.jsonl"
    )
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    print(f"Generated output file path for sample {sample_num}:", output_file_path)

    # save all parameters to the output file
    with open(output_file_path, "w") as f:
        f.write(json.dumps(args.__dict__ | test_case | timestamp) + "\n")

    # Dynamically import and run the selected jailbreak tactic
    try:
        run_function = run.get_custom_run(args.jailbreak_tactic)
        if run_function is None:
            print(f"No custom run file found, using default for sample {sample_num}.")
            # Run the attack in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                run.run_attack, 
                test_case, 
                output_file_path, 
                target_generate, 
                attacker_generate, 
                args.jailbreak_tactic,
                evaluator_generate 
            )
        else:
            print(f"Custom run file found, using it for sample {sample_num}.")
            # Run the custom function in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                run_function,
                test_case,
                output_file_path,
                target_generate,
                attacker_generate
            )
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Failed to run jailbreak tactic '{args.jailbreak_tactic}' for sample {sample_num}: {str(e)}")

# Main async function to run all samples in parallel
async def run_all_samples():
    tasks = []
    for i in range(args.samples):
        tasks.append(run_sample(i+1))
    
    await asyncio.gather(*tasks)
    print(f"Completed all {args.samples} samples")

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_all_samples())
