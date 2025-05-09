import os
import json
from utils.generate import generate
from openai import OpenAI
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up the client
client = OpenAI(
    base_url=os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

# The test message
messages = [
    {"role": "system", "content": "You are a helpful assistant. Be thorough in your responses and explain your thinking."},
    {"role": "user", "content": "What is the square root of 144 and how do you calculate it?"}
]

# Define different reasoning settings to test
reasoning_options = [
    "none",    # No reasoning
    "low",     # Low reasoning effort
    "medium",  # Medium reasoning effort
    "high",    # High reasoning effort
]

# Debug function to examine the structure of response objects
def debug_obj(obj, name="response", max_depth=3, current_depth=0):
    """Recursively print object attributes up to max_depth."""
    if current_depth > max_depth:
        return
    
    indent = "  " * current_depth
    print(f"{indent}{name} type: {type(obj)}")
    
    if hasattr(obj, "__dict__"):
        for k in obj.__dict__:
            if not k.startswith("_"):  # Skip private attributes
                v = getattr(obj, k)
                if isinstance(v, (str, int, float, bool, type(None))):
                    if isinstance(v, str) and len(v) > 100:
                        print(f"{indent}  {k}: {v[:100]}... (truncated)")
                    else:
                        print(f"{indent}  {k}: {v}")
                else:
                    debug_obj(v, k, max_depth, current_depth + 1)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                if isinstance(v, str) and len(v) > 100:
                    print(f"{indent}  {k}: {v[:100]}... (truncated)")
                else:
                    print(f"{indent}  {k}: {v}")
            else:
                debug_obj(v, k, max_depth, current_depth + 1)
    elif isinstance(obj, list) and len(obj) > 0:
        print(f"{indent}  list with {len(obj)} items")
        if current_depth < max_depth:
            for i, item in enumerate(obj[:3]):  # Print first 3 items
                debug_obj(item, f"{name}[{i}]", max_depth, current_depth + 1)
            if len(obj) > 3:
                print(f"{indent}  ... ({len(obj) - 3} more items)")

# Test all reasoning options for Claude
def test_claude_reasoning():
    model = "anthropic/claude-3.7-sonnet"
    thinking_model = "anthropic/claude-3.7-sonnet:thinking"
    
    print("\n==== Testing Claude Standard Model ====")
    print(f"Model: {model}")
    
    for reasoning in reasoning_options:
        print(f"\n--- Testing with reasoning={reasoning} ---")
        
        try:
            # Test with different reasoning settings
            print(f"Generating response with {model} and reasoning={reasoning}")
            result = generate(messages, client, model, reasoning=reasoning)
            
            # Check if result is a tuple with content and usage data
            if isinstance(result, tuple) and len(result) >= 2:
                content, usage_data = result
                
                # Debug print the content type and first part
                print(f"Response type: {type(content)}")
                
                # Handle different content types
                if isinstance(content, dict):
                    print("Response is a dictionary with keys:", content.keys())
                    if "content" in content:
                        print(f"Content: {content['content'][:100]}...")
                    if "reasoning" in content:
                        print(f"Reasoning detected! Length: {len(content['reasoning'])}")
                        print(f"Reasoning preview: {content['reasoning'][:100]}...")
                else:
                    print(f"Content: {str(content)[:100]}...")
                
                # Print token usage
                print(f"Token usage: {json.dumps(usage_data, indent=2)}")
                
                # Check specifically for reasoning tokens
                if usage_data and "reasoning_tokens" in usage_data:
                    print(f"Reasoning tokens: {usage_data['reasoning_tokens']}")
                else:
                    print("No reasoning tokens reported in usage data")
            else:
                print(f"Unexpected result format: {result}")
                
        except Exception as e:
            print(f"Error with {reasoning}: {str(e)}")
    
    print("\n==== Testing Claude Thinking Variant ====")
    print(f"Model: {thinking_model}")
    
    for reasoning in reasoning_options:
        print(f"\n--- Testing with reasoning={reasoning} ---")
        
        try:
            # Test with different reasoning settings
            print(f"Generating response with {thinking_model} and reasoning={reasoning}")
            result = generate(messages, client, thinking_model, reasoning=reasoning)
            
            # Check if result is a tuple with content and usage data
            if isinstance(result, tuple) and len(result) >= 2:
                content, usage_data = result
                
                # Debug print the content type and first part
                print(f"Response type: {type(content)}")
                
                # Handle different content types
                if isinstance(content, dict):
                    print("Response is a dictionary with keys:", content.keys())
                    if "content" in content:
                        print(f"Content: {content['content'][:100]}...")
                    if "reasoning" in content:
                        print(f"Reasoning detected! Length: {len(content['reasoning'])}")
                        print(f"Reasoning preview: {content['reasoning'][:100]}...")
                else:
                    print(f"Content: {str(content)[:100]}...")
                
                # Print token usage
                print(f"Token usage: {json.dumps(usage_data, indent=2)}")
                
                # Check specifically for reasoning tokens
                if usage_data and "reasoning_tokens" in usage_data:
                    print(f"Reasoning tokens: {usage_data['reasoning_tokens']}")
                else:
                    print("No reasoning tokens reported in usage data")
            else:
                print(f"Unexpected result format: {result}")
                
        except Exception as e:
            print(f"Error with {reasoning}: {str(e)}")

# Test direct API call to see raw response structure
def test_direct_api_call():
    model = "anthropic/claude-3.7-sonnet:thinking"
    
    print("\n==== Testing Direct API Call ====")
    print(f"Model: {model}")
    
    try:
        # Make a direct API call to see the raw response structure
        # We'll use the extra_body parameter to request reasoning
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            extra_body={
                "reasoning": {
                    "max_tokens": 4000,
                    "exclude": False  # Include reasoning in output
                }
            }
        )
        
        # Debug the response structure
        print("\nResponse object structure:")
        debug_obj(response)
        
        # Check if we can find reasoning content
        if hasattr(response, 'choices') and len(response.choices) > 0:
            message = response.choices[0].message
            print("\nMessage attributes:")
            for attr in dir(message):
                if not attr.startswith('_'):  # Skip private attributes
                    value = getattr(message, attr)
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {attr}: {value[:100]}... (truncated)")
                    else:
                        print(f"  {attr}: {value}")
            
            # Check for specific attributes that might contain reasoning
            if hasattr(message, 'reasoning'):
                reasoning = message.reasoning
                print(f"\nReasoning found: {reasoning[:200]}...")
            elif hasattr(message, 'thinking'):
                thinking = message.thinking
                print(f"\nThinking found: {thinking[:200]}...")
            else:
                print("\nNo explicit reasoning or thinking attribute found")
                
        # Check token usage information
        if hasattr(response, 'usage'):
            print("\nUsage data:")
            for attr in dir(response.usage):
                if not attr.startswith('_'):
                    print(f"  {attr}: {getattr(response.usage, attr)}")
            
            # Check for reasoning tokens in completion details
            if hasattr(response.usage, 'completion_tokens_details'):
                details = response.usage.completion_tokens_details
                for attr in dir(details):
                    if not attr.startswith('_'):
                        print(f"  completion_tokens_details.{attr}: {getattr(details, attr)}")
                        
    except Exception as e:
        print(f"Error in direct API call: {str(e)}")

if __name__ == "__main__":
    # Test Claude reasoning
    test_claude_reasoning()
    
    # Test with direct API call to examine raw response
    test_direct_api_call() 