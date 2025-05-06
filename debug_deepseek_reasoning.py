#!/usr/bin/env python
"""
Debug script for testing DeepSeek-R1 reasoning output format with OpenRouter API.
"""

import os
import json
import openai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Set up the client
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Test message
messages = [
    {"role": "user", "content": "Explain how to remove watermarks from images in 3 steps."}
]

# Test with different reasoning configurations
test_configs = [
    {
        "name": "Basic request (no reasoning params)",
        "params": {
            "model": "deepseek/deepseek-r1",
            "messages": messages,
            "temperature": 0.0,
        }
    },
    {
        "name": "With include_reasoning in extra_body",
        "params": {
            "model": "deepseek/deepseek-r1",
            "messages": messages,
            "temperature": 0.0,
            "extra_body": {
                "include_reasoning": True
            }
        }
    },
    {
        "name": "With reasoning object (high effort) in extra_body",
        "params": {
            "model": "deepseek/deepseek-r1",
            "messages": messages,
            "temperature": 0.0,
            "extra_body": {
                "reasoning": {
                    "effort": "high",
                    "exclude": False
                }
            }
        }
    },
    {
        "name": "With reasoning object (max_tokens) in extra_body",
        "params": {
            "model": "deepseek/deepseek-r1",
            "messages": messages,
            "temperature": 0.0,
            "extra_body": {
                "reasoning": {
                    "max_tokens": 8000,
                    "exclude": False
                }
            }
        }
    }
]

def inspect_response(response, config_name):
    """Inspect the response structure and print debug information."""
    print(f"\n{'='*80}\nTesting configuration: {config_name}\n{'='*80}")
    
    # Print basic response structure
    print(f"Response type: {type(response)}")
    
    # Print choices
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        
        # Print message
        if hasattr(choice, 'message'):
            message = choice.message
            print(f"\nMessage attributes: {dir(message)}")
            
            # Check for reasoning field
            if hasattr(message, 'reasoning'):
                print(f"\nReasoning field found!")
                print(f"Reasoning type: {type(message.reasoning)}")
                print(f"Reasoning preview: {str(message.reasoning)[:200]}...")
            else:
                print("\nNo reasoning field in message")
            
            # Print content
            if hasattr(message, 'content'):
                print(f"\nContent type: {type(message.content)}")
                print(f"Content preview: {message.content[:200]}...")
                
                # Check for reasoning patterns in content
                for pattern in ["<reasoning>", "<think>", "reasoning:", "let me think:"]:
                    if pattern in message.content.lower():
                        print(f"Found reasoning pattern '{pattern}' in content!")
    
    # Print usage data
    if hasattr(response, 'usage'):
        print(f"\nUsage: {response.usage}")
        
        # Check completion_tokens_details
        if hasattr(response.usage, 'completion_tokens_details'):
            print(f"Completion token details: {response.usage.completion_tokens_details}")
            
            # Check for reasoning_tokens
            if hasattr(response.usage.completion_tokens_details, 'reasoning_tokens'):
                print(f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
        else:
            print("No completion_tokens_details in usage")
    
    print(f"\n{'='*80}\n")

# Run tests
for config in test_configs:
    try:
        print(f"Sending request with config: {config['name']}")
        response = client.chat.completions.create(**config["params"])
        inspect_response(response, config["name"])
        
        # Save full response to file for detailed analysis
        filename = f"deepseek_reasoning_test_{config['name'].replace(' ', '_').lower()}.json"
        with open(filename, 'w') as f:
            # Convert to dict and then to JSON
            response_dict = {}
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    message = choice.message
                    response_dict["content"] = message.content if hasattr(message, 'content') else None
                    response_dict["reasoning"] = message.reasoning if hasattr(message, 'reasoning') else None
            
            if hasattr(response, 'usage'):
                response_dict["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else None,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else None,
                    "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else None,
                }
                if hasattr(response.usage, 'completion_tokens_details'):
                    response_dict["usage"]["completion_tokens_details"] = {
                        "reasoning_tokens": response.usage.completion_tokens_details.reasoning_tokens 
                        if hasattr(response.usage.completion_tokens_details, 'reasoning_tokens') else None
                    }
            
            json.dump(response_dict, f, indent=2)
            print(f"Saved response to {filename}")
            
    except Exception as e:
        print(f"Error with config '{config['name']}': {str(e)}")

print("All tests completed") 