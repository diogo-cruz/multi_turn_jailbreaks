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
    elif model.startswith("qwen/"):
        return "qwen"
    elif model.startswith("x-ai/grok"):
        return "grok"
    else:
        return "unknown"

def is_thinking_variant(model):
    """Check if the model is a thinking variant."""
    return ":thinking" in model

def is_qwen3_model(model):
    """Check if the model is a Qwen3 model that supports the /think and /no_think tags."""
    return model.startswith("qwen/qwen3-")

def get_model_context_window(client, model):
    """Get the context window size for a specific model.
    Fetches from the API or uses cached value if available."""
    if model in MODEL_CONTEXT_CACHE:
        return MODEL_CONTEXT_CACHE[model]
    
    try:
        model_info = client.models.retrieve(model)
        context_length = getattr(model_info, 'context_length', MAX_TOKENS)
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
    if (hasattr(response.usage, 'completion_tokens_details') and 
        hasattr(response.usage.completion_tokens_details, 'reasoning_tokens')):
        usage_data['reasoning_tokens'] = response.usage.completion_tokens_details.reasoning_tokens
    
    # Print the usage data (can be modified to save to file/database)
    print(f"Token usage: {json.dumps(usage_data, indent=2)}")
    
    return usage_data

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
            prompt_tokens = int(context_window * 0.1)  # Assume 10% of context used for prompt
            print(f"No usage data available, estimating prompt tokens: {prompt_tokens}")
    except Exception as e:
        print(f"Error in probe request: {e}")
        # Conservative fallback
        prompt_tokens = int(context_window * 0.1)
        print(f"Error measuring prompt tokens, using estimate: {prompt_tokens}")
    
    # Calculate available tokens for the response
    available_tokens = max(1, context_window - prompt_tokens)
    print(f"Available tokens for completion: {available_tokens}")
    
    # Base args for all requests
    base_args = {
        "model": model,
        "messages": messages.copy(),  # Copy to avoid modifying the original
        "temperature": temperature,
        "response_format": {"type": "json_object"} if json_format else {"type": "text"},
        "top_p": top_p,
        "max_tokens": available_tokens,  # Use available tokens instead of fixed MAX_TOKENS
    }
    
    # Helper function to process the response
    def process_response(response):
        # Extract and save usage data
        usage_data = extract_usage_data(response)
        
        if response.choices is None:
            return str(response.error), usage_data
            
        content = response.choices[0].message.content
        
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
                        return extract_json(content), usage_data
                else:
                    return extract_json(content), usage_data
        
        return content, usage_data
    
    # If reasoning is None, make a standard request
    if reasoning is None:
        response = client.chat.completions.create(**base_args)
        return process_response(response)
    
    # Get model family and check if it's a thinking variant
    model_family = get_model_family(model)
    is_thinking = is_thinking_variant(model)
    
    # More explicit validation for unknown models
    if model_family == "unknown" and reasoning == "none":
        raise ValueError(f"Model {model} is not in the known list of models that support no-reasoning mode")
    
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
            
            response = client.chat.completions.create(**base_args)
            return process_response(response)
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
                    "exclude": False  # Include reasoning in output
                }
            }
            base_args["extra_body"] = reasoning_args
            response = client.chat.completions.create(**base_args)
            return process_response(response)
    
    # Handle "none" reasoning level - true "no reasoning" for supported models
    if reasoning == "none":
        # For models that support no reasoning at all
        if model in NO_REASONING_SUPPORTED_MODELS:
            # Already using the non-thinking variant, so we're good
            response = client.chat.completions.create(**base_args)
            return process_response(response)
        
        # For thinking variants of models that support no-reasoning
        elif model in THINKING_VARIANTS:
            # Use exclude parameter to hide reasoning
            reasoning_args = {
                "reasoning": {
                    "exclude": True  # Hide reasoning in output
                }
            }
            base_args["extra_body"] = reasoning_args
            response = client.chat.completions.create(**base_args)
            return process_response(response)
        
        # For models that always think but can hide it
        elif model in ALWAYS_REASONING_MODELS:
            reasoning_args = {
                "reasoning": {
                    "exclude": True  # Hide reasoning in output
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
        response = client.chat.completions.create(**base_args)
        return process_response(response)
    
    # Invalid reasoning value
    else:
        raise ValueError(f"Invalid reasoning value: {reasoning}. Must be one of: none, low, medium, high")

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
