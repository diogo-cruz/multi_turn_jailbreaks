import os
import datetime
import argparse
import openai
import json
import importlib
from dotenv import load_dotenv
from utils import generate, run, generate_score_rubric


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
    "--target-base-url", 
    type=str, 
    help="The target model's base URL for the OpenAI API", 
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
    "--attacker-base-url",
    type=str,
    help="The attacker model's base URL for the OpenAI API",
    default="https://openrouter.ai/api/v1",
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


if args.gen_score_rubric:
    test_cases_dir = "test_cases"
    test_cases = [d for d in os.listdir(test_cases_dir) if os.path.isdir(os.path.join(test_cases_dir, d))] if args.gen_score_rubric_test_cases is None else args.gen_score_rubric_test_cases

    for t in test_cases:
        print(f"Generating score rubric for {t}")
        test_case_path = os.path.join(test_cases_dir, t, "multi_turn.json")
        with open(test_case_path, "r") as f:
            test_case = json.load(f)
        
        goal = test_case["task"]
        success_condition = test_case.get("success_condition", None)
        criteria = generate_score_rubric.generate_rubric(goal, attacker_generate, success_condition)

        score_rubric_path = os.path.join(test_cases_dir, t, "score_rubric.json")
        with open(score_rubric_path, "w") as file:
            json.dump({"score_rubric": criteria}, file, indent=2)
        
# Load the appropriate test case file based on whether it's single or multi turn
test_case_file = f"{args.turn_type}.json"
test_case_path = os.path.join("test_cases", args.test_case, test_case_file)

with open(test_case_path, "r") as f:
    test_case = json.load(f)

test_case_score_rubric_path = os.path.join("test_cases", args.test_case, "score_rubric.json")

with open(test_case_score_rubric_path, "r") as f:
    test_case_score_rubric = json.load(f)

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
        run.run_attack(test_case, test_case_score_rubric, output_file_path, target_generate, attacker_generate, args.jailbreak_tactic)
    else:
        print("Custom run file found, using it.")
        run_function(test_case, test_case_score_rubric, output_file_path, target_generate, attacker_generate)
except (ImportError, AttributeError) as e:
    raise ValueError(f"Failed to run jailbreak tactic '{args.jailbreak_tactic}': {str(e)}")
