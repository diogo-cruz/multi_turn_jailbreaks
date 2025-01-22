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

parser = argparse.ArgumentParser()
parser.add_argument(
    "--target-base-url", type=str, help="The target model's base URL for the OpenAI API"
)
parser.add_argument(
    "--target-model", type=str, help="The target model name", default="gpt-4o"
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
    "--test-case", type=str, help="Path to the test case JSON file", required=True
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


def target_generate(messages, **kwargs):
    return generate(messages, client=target_client, model=target_model, **kwargs)


attacker_client = openai.OpenAI(base_url=args.attacker_base_url)
attacker_model = args.attacker_model


def attacker_generate(messages, **kwargs):
    return generate(messages, client=attacker_client, model=attacker_model, **kwargs)


with open(f"./test_cases/{args.test_case}.json", "r") as f:
    test_case = json.load(f)

current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

output_file_path = (
    f"./results/{args.jailbreak_tactic}_{args.test_case}_{current_time}.jsonl"
)
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
