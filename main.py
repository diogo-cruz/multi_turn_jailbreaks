import os
import datetime
import argparse
import openai
import json
import importlib
from dotenv import load_dotenv
from utils import generate, run

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
    "--target-base-url", type=str, help="The target model's base URL for the OpenAI API"
)
parser.add_argument(
    "--target-model", type=str, help="The target model name", default="gpt-4o"
)
parser.add_argument(
    "--target-temp", type=float, help="The temperature to use for the target model", default=0.0
)
parser.add_argument(
    "--attacker-base-url",
    type=str,
    help="The attacker model's base URL for the OpenAI API",
)
parser.add_argument(
    "--attacker-model", type=str, help="The attacker model name", default="gpt-4o"
)
parser.add_argument(
    "--attacker-temp", type=float, help="The temperature to use for the attacker model", default=0.0
)
parser.add_argument(
    "--test-case", 
    type=str, 
    help="Name of the test case to run", 
    choices=TEST_CASES,
    required=True
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
args = parser.parse_args()

if not run.has_single_turn(args.jailbreak_tactic) and args.turn_type == 'single_turn':
    print(f"Skipping single turn for '{args.jailbreak_tactic}', as it does not have a single-turn implementation.")
    # Exit the program
    exit(0)

target_client = openai.OpenAI(base_url=args.target_base_url)
target_model = args.target_model
target_temp = args.target_temp


def target_generate(messages, **kwargs):
    return generate(messages, client=target_client, model=target_model, temperature=target_temp, **kwargs)


attacker_client = openai.OpenAI(base_url=args.attacker_base_url)
attacker_model = args.attacker_model
attacker_temp = args.attacker_temp


def attacker_generate(messages, temperature=attacker_temp, **kwargs):
    return generate(messages, client=attacker_client, model=attacker_model, 
    temperature=temperature, **kwargs)


# Load the appropriate test case file based on whether it's single or multi turn
test_case_file = f"{args.turn_type}.json"
test_case_path = os.path.join("test_cases", args.test_case, test_case_file)

with open(test_case_path, "r") as f:
    test_case = json.load(f)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
timestamp = {"timestamp": current_time}

output_file_path = (
    f"./results/{args.jailbreak_tactic}_{args.test_case}_{args.turn_type}_{current_time}.jsonl"
)
# target_model_name = args.target_model.split("/")[-1]
# output_file_path = (
#     f"./results/jaeha/{args.jailbreak_tactic}/{args.jailbreak_tactic}_{args.test_case}_{args.turn_type}_{target_model_name}_deterministic.jsonl"
# )
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
print("Generated Output file path:", output_file_path)

# save all parameters to the output file
with open(output_file_path, "w") as f:
    f.write(json.dumps(args.__dict__ | test_case | timestamp) + "\n")

# Dynamically import and run the selected jailbreak tactic
try:
    run_function = run.get_custom_run(args.jailbreak_tactic)
    if run_function is None:
        print("No custom run file found, using default.")
        run.run_attack(test_case, output_file_path, target_generate, attacker_generate, args.jailbreak_tactic)
    else:
        print("Custom run file found, using it.")
        run_function(test_case, output_file_path, target_generate, attacker_generate)
except (ImportError, AttributeError) as e:
    raise ValueError(f"Failed to run jailbreak tactic '{args.jailbreak_tactic}': {str(e)}")
