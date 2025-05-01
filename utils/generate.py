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

# Qwen models that use prompt tags to control reasoning
QWEN_MODELS = [
    "qwen/qwen3-7b",
    "qwen/qwen3-14b",
    "qwen/qwen3-30b-a3b",
    "qwen/qwen3-72b"
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
    "qwen/qwq-32b"
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
    else:
        return "unknown"

def is_thinking_variant(model):
    """Check if the model is a thinking variant."""
    return ":thinking" in model

def is_qwen_model(model):
    """Check if the model is a Qwen model."""
    return model in QWEN_MODELS

def generate(messages, client, model, temperature=0, top_p=1, json_format=False, reasoning=None):
    # Base args for all requests
    base_args = {
        "model": model,
        "messages": messages.copy(),  # Copy to avoid modifying the original
        "temperature": temperature,
        "response_format": {"type": "json_object"} if json_format else {"type": "text"},
        "top_p": top_p,
        "max_tokens": MAX_TOKENS,
    }
    
    # Helper function to process the response
    def process_response(response):
        if response.choices is None:
            return str(response.error)
            
        content = response.choices[0].message.content
        
        if json_format:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # A common error is the response trying to escape speech marks
                if "Invalid \\escape" in e.msg:
                    print("Invalid escape character found, attempting to fix...")
                    content = content.replace("\\'", "'").replace('\\"', '"')
                    try:
                        return json.loads(content)
                    except:
                        return extract_json(content)
                else:
                    return extract_json(content)
        
        return content
    
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
    
    # Special handling for Qwen models (using prompt tags)
    if model_family == "qwen" and is_qwen_model(model):
        if reasoning == "none":
            # For Qwen, inject the /no_think tag in the system message or prepend it to the first message
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
            
            # Still add reasoning parameters for token budget control
            reasoning_tokens = calculate_reasoning_tokens(reasoning)
            reasoning_args = {
                "reasoning": {
                    "max_tokens": reasoning_tokens,
                    "exclude": True  # Don't show reasoning in output
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
                    "exclude": True
                }
            }
            base_args["extra_body"] = reasoning_args
            response = client.chat.completions.create(**base_args)
            return process_response(response)
        
        # For models that always think but can hide it
        elif model in ALWAYS_REASONING_MODELS:
            reasoning_args = {
                "reasoning": {
                    "exclude": True
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
        reasoning_tokens = calculate_reasoning_tokens(reasoning)
        
        # For OpenAI models, use the effort parameter
        if model_family == "openai":
            reasoning_args = {
                "reasoning": {
                    "effort": reasoning,
                    "exclude": True  # Don't show reasoning in output
                }
            }
        
        # For other models, use max_tokens for reasoning
        else:
            reasoning_args = {
                "reasoning": {
                    "max_tokens": reasoning_tokens,
                    "exclude": True  # Don't show reasoning in output
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
