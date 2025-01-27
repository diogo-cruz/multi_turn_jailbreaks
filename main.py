import os
import datetime
import argparse
import openai
import json
import importlib
from dotenv import load_dotenv
from utils import generate

# Load the API keys from the .env file
load_dotenv()

# Get available jailbreak tactics
JAILBREAK_TACTICS = [d for d in os.listdir('jailbreaks') 
                    if os.path.isdir(os.path.join('jailbreaks', d)) and 
                    os.path.exists(os.path.join('jailbreaks', d, 'run.py'))]

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
    "--single-turn",
    action="store_true",
    help="Run single-turn version of the test case instead of multi-turn"
)
parser.add_argument(
    "--jailbreak-tactic",
    type=str,
    help="The jailbreak tactic to use",
    choices=JAILBREAK_TACTICS,
    default="crescendomation",
)
args = parser.parse_args()


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
test_case_file = "single_turn.json" if args.single_turn else "multi_turn.json"
test_case_path = os.path.join("test_cases", args.test_case, test_case_file)

with open(test_case_path, "r") as f:
    test_case = json.load(f)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
turn_type = "single_turn" if args.single_turn else "multi_turn"

output_file_path = (
    f"./results/{args.jailbreak_tactic}_{args.test_case}_{turn_type}_{current_time}.jsonl"
)
# target_model_name = args.target_model.split("/")[-1]
# output_file_path = (
#     f"./results/jaeha/{args.jailbreak_tactic}/{args.jailbreak_tactic}_{args.test_case}_{turn_type}_{target_model_name}_deterministic.jsonl"
# )
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
print("Generated Output file path:", output_file_path)

# save all parameters to the output file
with open(output_file_path, "w") as f:
    f.write(json.dumps(args.__dict__ | test_case) + "\n")

# Dynamically import and run the selected jailbreak tactic
try:
    jailbreak_module = importlib.import_module(f"jailbreaks.{args.jailbreak_tactic}.run")
    run_function = getattr(jailbreak_module, f"run_{args.jailbreak_tactic}")
    run_function(test_case, output_file_path, target_generate, attacker_generate)
except (ImportError, AttributeError) as e:
    raise ValueError(f"Failed to run jailbreak tactic '{args.jailbreak_tactic}': {str(e)}")
