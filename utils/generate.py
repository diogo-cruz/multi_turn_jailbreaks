"""
LLM Generation Utility

This module provides a standardized interface for generating text from language models
using the OpenAI API format. It handles the core functionality of sending messages to 
models and processing their responses in a consistent way across the framework.

The primary function, 'generate', accepts a list of messages and other optional parameters
and returns the model's response. This abstraction allows the rest of the framework to
interact with different models in a consistent way, regardless of their specific API
implementation details.

This utility is used throughout the framework for both target model interaction (the model
being tested) and attacker model interaction (the model generating jailbreak prompts).
"""

import json
import re
import time

# Models that support truly disabling reasoning (no thinking at all)
NO_REASONING_SUPPORTED_MODELS = [
    # Gemini models (standard variants without ":thinking" suffix)
    "google/gemini-2.5-flash-preview",
    
    # Claude models (standard variants without ":thinking" suffix)
    "anthropic/claude-3.7-sonnet"
]

# Models that always think internally but can hide reasoning output
ALWAYS_REASONING_MODELS = [
    # OpenAI o-series
    "openai/o1", 
    "openai/o1-mini",
    "openai/o1-preview",
    "openai/o3", 
    "openai/o3-mini",
    "openai/o3-preview",
    "openai/o4-mini",
    "openai/o4-preview",
    
    # DeepSeek models
    "deepseek/deepseek-r1",
    
    # QwQ models (Qwen's reasoning-specific version)
    "qwen/qwq-32b",
    
    # xAI models
    "x-ai/grok-3-mini-beta"
]

# Qwen models that support reasoning control
QWEN_MODELS = [
    # Qwen3 models (support reasoning via /think and /no_think tags)
    "qwen/qwen3-0.6b-04-28:free",
    "qwen/qwen3-1.7b:free",
    "qwen/qwen3-4b:free",
    "qwen/qwen3-8b",
    "qwen/qwen3-14b",
    "qwen/qwen3-32b",
    "qwen/qwen3-30b-a3b",
    "qwen/qwen3-235b-a22b",
    
    # QwQ models (Qwen's reasoning-specific model)
    "qwen/qwq-32b",
    "qwen/qwq-32b-preview",
]

# Thinking variants of models
THINKING_VARIANTS = [
    "google/gemini-2.5-flash-preview:thinking",
    "anthropic/claude-3.7-sonnet:thinking"
]

# Maximum tokens to use (for calculating reasoning budgets)
MAX_TOKENS = 32000

# Effort ratios for different reasoning levels
EFFORT_RATIOS = {
    "low": 0.20,
    "medium": 0.50,
    "high": 0.80
}

# Cache for model context windows
MODEL_CONTEXT_CACHE = {}

def calculate_reasoning_tokens(effort):
    """Calculate the number of reasoning tokens based on effort level."""
    ratio = EFFORT_RATIOS[effort]
    tokens = int(MAX_TOKENS * ratio)
    
    # Clamp to OpenRouter's min/max values (1024-32000)
    return max(1024, min(tokens, 32000))

def get_model_family(model):
    """Determine which model family the model belongs to."""
    if model.startswith("openai/o"):
        return "openai"
    elif model.startswith("google/gemini"):
        return "gemini"
    elif model.startswith("anthropic/claude"):
        return "claude"
    elif model.startswith("deepseek/"):
        return "deepseek"
    elif model.startswith("qwen/") or model.startswith("qwen3-") or model.startswith("qwq-"):
        return "qwen"
    elif model.startswith("x-ai/grok"):
        return "grok"
    else:
        return "unknown"

def is_thinking_variant(model):
    """Check if the model is a thinking variant."""
    return ":thinking" in model

def is_qwen3_model(model):
    """Check if the model is a Qwen3 or QwQ model that supports reasoning capabilities."""
    # Handle both formats: with qwen/ prefix and without
    return (model.startswith("qwen/qwen3-") or 
            model.startswith("qwen3-") or 
            model.startswith("qwen/qwq-") or
            model.startswith("qwq-"))

def get_model_context_window(client, model):
    """Get the context window size for a specific model.
    Fetches from the API or uses cached value if available."""
    if model in MODEL_CONTEXT_CACHE:
        return MODEL_CONTEXT_CACHE[model]
    
    # Hardcoded context window sizes for common models
    # OpenAI models
    if model.startswith("openai/gpt-4") or model.startswith("openai/o"):
        if "mini" in model:
            context_length = 100000  # GPT-4o mini, o1-mini, etc.
        else:
            context_length = 100000  # GPT-4o, o1, etc.
        MODEL_CONTEXT_CACHE[model] = context_length
        return context_length
    
    # Other model families with known context sizes
    if model.startswith("anthropic/claude-3"):
        if "sonnet" in model:
            context_length = 150000
        elif "haiku" in model:
            context_length = 150000
        else:  # Opus
            context_length = 150000
        MODEL_CONTEXT_CACHE[model] = context_length
        return context_length
        
    if model.startswith("google/gemini"):
        context_length = 100000
        MODEL_CONTEXT_CACHE[model] = context_length
        return context_length
        
    if model.startswith("qwen/") or model.startswith("qwen3-") or model.startswith("qwq-"):
        context_length = 24000  # More conservative value for Qwen models
        MODEL_CONTEXT_CACHE[model] = context_length
        return context_length
    
    # Try API for other models
    try:
        model_info = client.models.retrieve(model)
        context_length = getattr(model_info, 'context_length', MAX_TOKENS)
        # Apply a safety margin to avoid hitting context limits
        context_length = int(context_length * 0.9)  # Use 90% of reported context length
        MODEL_CONTEXT_CACHE[model] = context_length
        return context_length
    except Exception as e:
        print(f"Warning: Failed to retrieve context length for {model}: {e}")
        # Don't store in cache if we got an error - use default but don't save it
        return MAX_TOKENS  # Fallback to default without caching the failure

def extract_usage_data(response):
    """Extract token usage data from a response."""
    if not hasattr(response, 'usage'):
        return {"available": False, "reason": "No usage data in response"}
    
    usage_data = {
        'available': True,
        'model': getattr(response, 'model', 'unknown'),
        'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
        'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
        'total_tokens': getattr(response.usage, 'total_tokens', 0),
        'cost': response.headers.get('x-openrouter-cost-usd', 'unknown') if hasattr(response, 'headers') else 'unknown'
    }
    
    # Extract reasoning tokens if available
    reasoning_tokens = 0
    
    # Check for completion_tokens_details with reasoning_tokens field first (proper API path)
    if (hasattr(response.usage, 'completion_tokens_details') and 
        hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')):
        reasoning_tokens = response.usage.completion_tokens_details.reasoning_tokens
        usage_data['reasoning_tokens'] = reasoning_tokens
        print(f"DEBUG: Found reasoning_tokens in completion_tokens_details: {reasoning_tokens}")
    else:
        print("DEBUG: No reasoning_tokens found in completion_tokens_details")
        
        # If this is a DeepSeek or Qwen model, check if we have reasoning content and estimate tokens
        model_name = usage_data['model'].lower()
        if ('deepseek' in model_name or 'qwen' in model_name) and hasattr(response, 'choices') and response.choices:
            # Check if reasoning exists as a direct attribute
            if hasattr(response.choices[0].message, 'reasoning'):
                reasoning_content = response.choices[0].message.reasoning
                # Estimate token count based on string length (rough approximation: ~4 chars per token)
                estimated_tokens = len(reasoning_content) // 4
                usage_data['reasoning_tokens'] = estimated_tokens
                print(f"DEBUG: Estimated reasoning tokens from content length: ~{estimated_tokens}")
                print(f"DEBUG: Reasoning content first 100 chars: {reasoning_content[:100]}...")
            
            # Check if reasoning exists in a 'thinking' attribute (Qwen might use this)
            elif hasattr(response.choices[0].message, 'thinking'):
                reasoning_content = response.choices[0].message.thinking
                estimated_tokens = len(reasoning_content) // 4
                usage_data['reasoning_tokens'] = estimated_tokens
                print(f"DEBUG: Found 'thinking' field in message content, estimated tokens: ~{estimated_tokens}")
                print(f"DEBUG: Thinking content first 100 chars: {reasoning_content[:100]}...")
            
            # Check if content contains reasoning wrapped in a special format for Qwen
            elif hasattr(response.choices[0].message, 'content'):
                content = response.choices[0].message.content
                
                # Try to find reasoning in Qwen's format: <thinking>...</thinking>
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    reasoning_content = thinking_match.group(1)
                    estimated_tokens = len(reasoning_content) // 4
                    usage_data['reasoning_tokens'] = estimated_tokens
                    print(f"DEBUG: Found reasoning in <thinking> tags, estimated tokens: ~{estimated_tokens}")
                
    # Enhanced model-specific checks
    model_name = usage_data['model'].lower()
    if 'deepseek' in model_name:
        print("DEBUG: DeepSeek model detected, checking for reasoning field")
        if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0], 'message'):
            message = response.choices[0].message
            
            # Check if reasoning exists directly in the message
            if hasattr(message, 'reasoning'):
                print(f"DEBUG: Found reasoning field in message (length={len(message.reasoning)})")
            
            # Check if content contains reasoning in a structured format
            if hasattr(message, 'content'):
                content = message.content
                print(f"DEBUG: Message content first 100 chars: {content[:100]}...")
    
    elif 'qwen' in model_name:
        print("DEBUG: Qwen model detected, checking for reasoning field")
        if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0], 'message'):
            message = response.choices[0].message
            
            # Check all attributes of the message to find reasoning
            for attr_name in dir(message):
                if attr_name.startswith('_'):  # Skip private attributes
                    continue
                    
                attr_value = getattr(message, attr_name, None)
                if attr_value and isinstance(attr_value, str) and len(attr_value) > 10:
                    print(f"DEBUG: Found potential reasoning in attribute '{attr_name}' (length={len(attr_value)})")
                    # First 50 chars of the attribute
                    print(f"DEBUG: {attr_name} content sample: {attr_value[:50]}...")
            
            # Check if content contains reasoning in Qwen's format
            if hasattr(message, 'content'):
                content = message.content
                print(f"DEBUG: Message content first 100 chars: {content[:100]}...")
                
                # Explicit pattern matching for Qwen reasoning formats
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    print(f"DEBUG: Found <thinking> tags in content")
    
    # Print the usage data (can be modified to save to file/database)
    print(f"Token usage: {json.dumps(usage_data, indent=2)}")
    
    return usage_data

def get_base_model(model):
    """Convert a thinking variant model to its base model by removing the :thinking suffix."""
    if is_thinking_variant(model):
        return model.split(":thinking")[0]
    return model

def generate(messages, client, model, temperature=0, top_p=1, json_format=False, reasoning=None):
    # Get the model's context window
    context_window = get_model_context_window(client, model)
    
    # Create a probe request to measure prompt tokens
    # We'll use max_tokens=1 to minimize token usage while still getting prompt_tokens count
    probe_args = {
        "model": model,
        "messages": messages.copy(),
        "max_tokens": 1,  # Just need enough to get a response
        "temperature": 0,
    }
    
    try:
        # Make a minimal probe request to get token counts
        probe_response = client.chat.completions.create(**probe_args)
        if hasattr(probe_response, 'usage') and hasattr(probe_response.usage, 'prompt_tokens'):
            prompt_tokens = probe_response.usage.prompt_tokens
            print(f"Prompt token count: {prompt_tokens}")
        else:
            # If no usage data, make a conservative estimate
            prompt_tokens = int(context_window * 0.2)  # Assume 20% of context used for prompt
            print(f"No usage data available, estimating prompt tokens: {prompt_tokens}")
    except Exception as e:
        print(f"Error in probe request: {e}")
        # Conservative fallback
        prompt_tokens = int(context_window * 0.2)
        print(f"Error measuring prompt tokens, using estimate: {prompt_tokens}")
    
    # Calculate available tokens for the response, ensure we don't exceed reasonable limits
    max_completion_tokens = min(16000, int(context_window * 0.75))  # Cap at 16k or 75% of context
    available_tokens = min(max_completion_tokens, max(1, context_window - prompt_tokens - 100))  # -100 for safety
    print(f"Available tokens for completion: {available_tokens}")
    
    # Base args for all requests
    base_args = {
        "model": model,
        "messages": messages.copy(),  # Copy to avoid modifying the original
        "temperature": temperature,
        "response_format": {"type": "json_object"} if json_format else {"type": "text"},
        "top_p": top_p,
        "max_tokens": available_tokens,
    }
    
    # Helper function to process the response
    def process_response(response):
        # Extract and save usage data
        usage_data = extract_usage_data(response)
        
        if response.choices is None or len(response.choices) == 0:
            error_msg = getattr(response, 'error', 'No choices returned and no error message')
            print(f"ERROR: No valid response choices returned: {error_msg}")
            return "I apologize, but I cannot provide the information you're looking for.", usage_data
            
        content = response.choices[0].message.content
        
        # Generic reasoning extraction that works with multiple models
        reasoning_content = None
        model_name = usage_data.get('model', '').lower()
        
        # Enhanced reasoning extraction with explicit handling per model type
        if hasattr(response.choices[0].message, 'reasoning'):
            reasoning_content = response.choices[0].message.reasoning
            print(f"DEBUG: Extracted reasoning from message.reasoning attribute")
        elif hasattr(response.choices[0].message, 'thinking'):
            reasoning_content = response.choices[0].message.thinking
            print(f"DEBUG: Extracted reasoning from message.thinking attribute")
        elif 'qwen' in model_name:
            # Look for Qwen-specific reasoning format in content
            if content:
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
                if thinking_match:
                    reasoning_content = thinking_match.group(1)
                    print(f"DEBUG: Extracted Qwen reasoning from <thinking> tags in content")
                    # Remove the tags from the visible content
                    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
                    print(f"DEBUG: Removed thinking tags from content")
        
        # If we found any reasoning content, return both content and reasoning
        if reasoning_content:
            print(f"DEBUG: Creating combined response with content and reasoning")
            return {"content": content, "reasoning": reasoning_content}, usage_data
        
        # Check for empty or null content
        if content is None or content.strip() == "":
            print("WARNING: Empty response content received")
            return "I apologize, but I received an empty response.", usage_data
        
        if json_format:
            try:
                return json.loads(content), usage_data
            except json.JSONDecodeError as e:
                # A common error is the response trying to escape speech marks
                if "Invalid \\escape" in e.msg:
                    print("Invalid escape character found, attempting to fix...")
                    content = content.replace("\\'", "'").replace('\\"', '"')
                    try:
                        return json.loads(content), usage_data
                    except:
                        print(f"Failed to parse JSON after escape fix: {content}")
                        return extract_json(content), usage_data
                else:
                    print(f"JSON decode error: {e.msg}")
                    print(f"Content: {content}")
                    return extract_json(content), usage_data
        
        return content, usage_data
    
    # Try to make the actual request with error handling and retry logic
    max_retries = 3
    retry_delay = 5  # seconds
    
    for retry_count in range(max_retries):
        try:
            # If reasoning is None, make a standard request
            if reasoning is None:
                response = client.chat.completions.create(**base_args)
                return process_response(response)
            
            # For reasoning requests, follow the existing code path...
            # Get model family and check if it's a thinking variant
            model_family = get_model_family(model)
            is_thinking = is_thinking_variant(model)
            
            # More explicit validation for unknown models
            if model_family == "unknown" and reasoning == "none":
                raise ValueError(f"Model {model} is not in the known list of models that support no-reasoning mode")
            
            # For "none" reasoning on thinking variants, convert to the base model
            original_model = model
            if reasoning == "none" and is_thinking:
                model = get_base_model(model)
                base_args["model"] = model
                print(f"DEBUG: Converted thinking variant '{original_model}' to base model '{model}' for reasoning=none")
            
            # Calculate reasoning tokens based on available tokens and effort level
            if reasoning in ["low", "medium", "high"]:
                ratio = EFFORT_RATIOS[reasoning]
                reasoning_tokens = max(1024, min(int(available_tokens * ratio), 32000))
            else:
                reasoning_tokens = 0
            
            # Special handling for Qwen models (using prompt tags)
            if model_family == "qwen" and is_qwen3_model(model):
                if reasoning == "none":
                    # For Qwen3, inject the /no_think tag in the system message or prepend it to the first message
                    if base_args["messages"][0]["role"] == "system":
                        base_args["messages"][0]["content"] = "/no_think " + base_args["messages"][0]["content"]
                    else:
                        # Insert a system message with the /no_think tag
                        base_args["messages"].insert(0, {"role": "system", "content": "/no_think"})
                    
                    try:
                        response = client.chat.completions.create(**base_args)
                        return process_response(response)
                    except Exception as e:
                        if retry_count < max_retries - 1:
                            print(f"API error with Qwen (attempt {retry_count+1}/{max_retries}): {str(e)}")
                            print(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            print(f"Failed after {max_retries} attempts. Last error: {str(e)}")
                            usage_data = {"available": False, "reason": f"API error after {max_retries} retries: {str(e)}"}
                            return f"I encountered an error while processing your request: {str(e)}", usage_data
                
                elif reasoning in ["low", "medium", "high"]:
                    # For explicit reasoning levels, use the /think tag and add reasoning token controls
                    if base_args["messages"][0]["role"] == "system":
                        base_args["messages"][0]["content"] = "/think " + base_args["messages"][0]["content"]
                    else:
                        # Insert a system message with the /think tag
                        base_args["messages"].insert(0, {"role": "system", "content": "/think"})
                    
                    # Add reasoning parameters for token budget control
                    reasoning_args = {
                        "reasoning": {
                            "max_tokens": reasoning_tokens,
                            "exclude": False,  # Include reasoning in output
                            "include_reasoning": True  # Redundant but might help with some API versions
                        }
                    }
                    base_args["extra_body"] = reasoning_args
                    
                    # Add debug logging to see what parameters we're sending
                    print(f"DEBUG: Qwen3 request with /think tag and parameters: {json.dumps(base_args, default=str)}")
                    
                    try:
                        response = client.chat.completions.create(**base_args)
                        return process_response(response)
                    except Exception as e:
                        if retry_count < max_retries - 1:
                            print(f"API error with Qwen reasoning (attempt {retry_count+1}/{max_retries}): {str(e)}")
                            print(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            print(f"Failed after {max_retries} attempts with reasoning. Last error: {str(e)}")
                            usage_data = {"available": False, "reason": f"API error after {max_retries} retries: {str(e)}"}
                            return f"I encountered an error while processing your request: {str(e)}", usage_data
            
            # Handle "none" reasoning level - true "no reasoning" for supported models
            if reasoning == "none":
                # For models that support no reasoning at all
                if model in NO_REASONING_SUPPORTED_MODELS:
                    # Already using the non-thinking variant, so we're good
                    response = client.chat.completions.create(**base_args)
                    return process_response(response)
                
                # For thinking variants of models that support no-reasoning
                # (This block is kept for compatibility with models that aren't in THINKING_VARIANTS
                # but might still use the :thinking suffix convention)
                elif is_thinking_variant(model):
                    # Use exclude parameter to hide reasoning
                    reasoning_args = {
                        "reasoning": {
                            "exclude": False  # Hide reasoning in output
                        }
                    }
                    base_args["extra_body"] = reasoning_args
                    response = client.chat.completions.create(**base_args)
                    return process_response(response)
                
                # For models that always think but can hide it
                elif model in ALWAYS_REASONING_MODELS:
                    reasoning_args = {
                        "reasoning": {
                            "exclude": False  # Hide reasoning in output
                        }
                    }
                    base_args["extra_body"] = reasoning_args
                    response = client.chat.completions.create(**base_args)
                    return process_response(response)
                    
                # For unsupported models, raise an error
                else:
                    raise ValueError(f"Model {model} does not support no-reasoning mode")
            
            # Handle specific reasoning effort levels
            elif reasoning in ["low", "medium", "high"]:
                # For OpenAI models, use the effort parameter
                if model_family == "openai":
                    reasoning_args = {
                        "reasoning": {
                            "effort": reasoning,
                            "exclude": False  # Include reasoning in output
                        }
                    }
                
                # For other models, use max_tokens for reasoning
                else:
                    reasoning_args = {
                        "reasoning": {
                            "max_tokens": reasoning_tokens,
                            "exclude": False  # Include reasoning in output
                        }
                    }
                
                base_args["extra_body"] = reasoning_args
                
                try:
                    response = client.chat.completions.create(**base_args)
                    return process_response(response)
                except Exception as e:
                    if retry_count < max_retries - 1:
                        print(f"API error (attempt {retry_count+1}/{max_retries}): {str(e)}")
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"Failed after {max_retries} attempts. Last error: {str(e)}")
                        usage_data = {"available": False, "reason": f"API error after {max_retries} retries: {str(e)}"}
                        return f"I encountered an error while processing your request: {str(e)}", usage_data
            
            # Invalid reasoning value
            else:
                raise ValueError(f"Invalid reasoning value: {reasoning}. Must be one of: none, low, medium, high")
        except Exception as e:
            if retry_count < max_retries - 1:
                print(f"Error during API call (attempt {retry_count+1}/{max_retries}): {str(e)}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                print(f"ERROR in generate request (failed after {max_retries} attempts): {str(e)}")
                # Return a fallback response with empty usage data
                usage_data = {"available": False, "reason": f"API error after {max_retries} retries: {str(e)}"}
                return f"I encountered an error while processing your request: {str(e)}", usage_data

def extract_json(text):
    # Try to find JSON-like content within triple backticks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # If no triple backticks, try to find outer-most curly braces
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None

    # Try to parse the extracted string as JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("Non-JSON response received:\n", text)
        raise
