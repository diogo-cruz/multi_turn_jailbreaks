import os
import sys
import json
import time
import argparse
import re
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Test Qwen 3 reasoning capabilities")
    parser.add_argument("--model", type=str, default="qwen/qwen3-8b", help="Model to test")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    parser.add_argument("--timeout", type=int, default=60, help="API request timeout in seconds")
    args = parser.parse_args()

    # Set up basic auth for API calls
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize the OpenAI client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=args.timeout
    )

    # Basic prompt for testing
    prompt = "What is the capital of France?"

    # Define test cases
    test_cases = [
        {
            "name": "basic_request_no_reasoning",
            "description": "Basic request with no reasoning parameters",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "params": {}
        },
        {
            "name": "basic_request_with_slash_think",
            "description": "Using /think tag in system message",
            "messages": [
                {"role": "system", "content": "/think"},
                {"role": "user", "content": prompt}
            ],
            "params": {}
        },
        {
            "name": "think_tag_with_reasoning_object",
            "description": "Using /think and reasoning parameter",
            "messages": [
                {"role": "system", "content": "/think"},
                {"role": "user", "content": prompt}
            ],
            "params": {
                "extra_body": {
                    "reasoning": {
                        "max_tokens": 1024,
                        "exclude": False
                    }
                }
            }
        },
        {
            "name": "high_effort_reasoning",
            "description": "Using /think with high effort reasoning",
            "messages": [
                {"role": "system", "content": "/think I want you to think deeply about this question"},
                {"role": "user", "content": prompt}
            ],
            "params": {
                "extra_body": {
                    "reasoning": {
                        "max_tokens": 2048,
                        "exclude": False,
                        "include_reasoning": True
                    }
                }
            }
        },
        {
            "name": "hard_question_with_reasoning",
            "description": "Hard question that needs reasoning",
            "messages": [
                {"role": "system", "content": "/think"},
                {"role": "user", "content": "If x² + 10x + 25 = 0, what is the value of x?"}
            ],
            "params": {
                "extra_body": {
                    "reasoning": {
                        "max_tokens": 1024,
                        "exclude": False
                    }
                }
            }
        }
    ]

    # Run tests
    for test in test_cases:
        print(f"\n[TEST] {test['name']}: {test['description']}")
        
        # Setup base parameters
        params = {
            "model": args.model,
            "messages": test["messages"].copy(),
            "temperature": 0,
            "max_tokens": 1024
        }
        
        # Add any additional parameters
        for key, value in test["params"].items():
            params[key] = value
            
        print(f"Request parameters: {json.dumps(params, indent=2, default=str)}")
        
        try:
            # Make the API call
            start_time = time.time()
            response = client.chat.completions.create(**params)
            duration = time.time() - start_time
            
            # Print basic response info
            print(f"Response time: {duration:.2f} seconds")
            print(f"Model: {getattr(response, 'model', 'Unknown')}")
            
            # Check for any reasoning content
            if hasattr(response, 'choices') and response.choices:
                message = response.choices[0].message
                
                # Print the visible response content
                content = message.content if hasattr(message, 'content') else "No content"
                print(f"Response content: {content[:500]}...")
                
                # Check for reasoning field
                if hasattr(message, 'reasoning'):
                    print(f"Reasoning found (attribute): {message.reasoning[:500]}...")
                elif hasattr(message, 'thinking'):
                    print(f"Thinking found (attribute): {message.thinking[:500]}...")
                else:
                    # Try to extract reasoning from content
                    if "<thinking>" in content:
                        match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                        if match:
                            reasoning = match.group(1)
                            print(f"Reasoning extracted from tags: {reasoning[:500]}...")
                    else:
                        print("No reasoning content found")
                
                # Debug: dump all message attributes
                if args.debug:
                    print("\nDEBUG: Message attributes:")
                    for attr in dir(message):
                        if not attr.startswith('_'):  # Skip private attributes
                            value = getattr(message, attr)
                            if isinstance(value, (str, int, float, bool)) or value is None:
                                print(f"  {attr}: {value}")
                            else:
                                print(f"  {attr}: {type(value)}")
            
            # Usage information
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"\nUsage:")
                print(f"  Prompt tokens: {getattr(usage, 'prompt_tokens', 'N/A')}")
                print(f"  Completion tokens: {getattr(usage, 'completion_tokens', 'N/A')}")
                print(f"  Total tokens: {getattr(usage, 'total_tokens', 'N/A')}")
                
                # Check for reasoning tokens
                if hasattr(usage, 'completion_tokens_details'):
                    details = usage.completion_tokens_details
                    if hasattr(details, 'reasoning_tokens'):
                        print(f"  Reasoning tokens: {details.reasoning_tokens}")
                    else:
                        print("  No reasoning tokens in completion_tokens_details")
                else:
                    print("  No completion_tokens_details in usage")
            
        except Exception as e:
            print(f"Error during API call: {str(e)}")
            continue
        
        print("\n" + "-"*80)

if __name__ == "__main__":
    main() 