"""
Rate-Limited LLM Generation Utility

This module extends the base generation utility with rate limiting and error handling
capabilities specifically designed for working with free-tier language model APIs. It
implements exponential backoff retry logic for handling rate limit errors (HTTP 429)
and provides robust error handling for various API issues.

Key features:
- Automatic handling of rate limit errors with configurable retry parameters
- Exponential backoff algorithm to gradually increase wait times between retries
- Comprehensive error detection and handling for various API response codes
- Detailed logging of API interactions and error conditions
- Support for multiple model providers with different rate limit implementations

This utility is particularly useful when working with free-tier API services that
impose strict rate limits, allowing the framework to gracefully handle these
constraints and continue operation despite temporary API limitations.
"""

import json
import re
import time
import random
import sys
import traceback
import os

# Maximum number of retries for rate limit errors - increased to 15
MAX_RETRIES = 15

# Per-model specific delays (in seconds)
MODEL_SPECIFIC_DELAYS = {
    # Format: "model_id": minimum_delay_seconds
    "google/gemini": 10,  # Gemini models need more space between requests
    "nvidia/llama": 8,    # Nvidia models also need more spacing
    "meta-llama/llama-4": 5,  # Meta models
    "mistralai/mistral": 3,   # Mistral models
}

def get_model_specific_delay(model_name):
    """Get a model-specific delay based on the model name prefix"""
    for prefix, delay in MODEL_SPECIFIC_DELAYS.items():
        if prefix in model_name:
            return delay
    return 1  # Default delay if no specific model match

def generate(messages, client, model, temperature=0, top_p=1, json_format=False):
    """
    A rate-limit aware wrapper for generating completions that implements
    exponential backoff for handling rate limits and other errors.
    """
    retry_count = 0
    base_wait_time = 5  # starting wait time in seconds
    last_error = None
    
    # Add model-specific delay at the start if this is a known model that needs spacing
    model_delay = get_model_specific_delay(model)
    if model_delay > 1:
        time.sleep(model_delay)
    
    while retry_count < MAX_RETRIES:
        try:
            # Add a small random delay before each request to stagger requests when running in parallel
            if retry_count > 0:
                stagger_delay = random.uniform(1, 3) * retry_count
                print(f"Adding stagger delay of {stagger_delay:.2f} seconds before retry...", file=sys.stderr)
                time.sleep(stagger_delay)
                
            # Debug information about the request
            print(f"Sending request to model: {model}", file=sys.stderr)
            
            # Get auth token from environment for debugging
            auth_token = os.environ.get('OPENAI_API_KEY', 'Not Set')
            if auth_token != 'Not Set':
                token_prefix = auth_token[:5] if len(auth_token) > 5 else "too_short"
                token_suffix = auth_token[-5:] if len(auth_token) > 5 else "too_short" 
                print(f"Using auth token: {token_prefix}...{token_suffix}", file=sys.stderr)
            
            # Create a more robust headers dict with Authorization
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "HTTP-Referer": "https://multi_turn_jailbreaks",
                "X-Title": "Multi-Turn Jailbreak Testing"
            }
                
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "text"}
                if not json_format
                else {"type": "json_object"},
                top_p=top_p,
                extra_headers=headers
            )
            
            if response.choices is None:
                raise Exception(f"Empty response received: {str(response)}")
            
            if json_format:
                content = response.choices[0].message.content
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    # A common error is the response trying to escape speech marks, such as \' or \"
                    # This is not valid JSON, so we need to remove the escape characters
                    if "Invalid \\escape" in e.msg:
                        print("Invalid escape character found, attempting to fix...", file=sys.stderr)
                        content = content.replace("\\'", "'").replace('\\"', '"')
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            # If still failing, try to extract JSON
                            extracted = extract_json(content)
                            if extracted:
                                return extracted
                            raise Exception(f"Failed to parse JSON after fixing escape characters: {content}")
                    else:
                        extracted = extract_json(content)
                        if extracted:
                            return extracted
                        raise Exception(f"Invalid JSON response: {content}. Error: {e}")
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_message = str(e)
            last_error = e
            retry_count += 1
            
            # Check for OpenRouter specific error messages
            if "entity not found" in error_message.lower():
                print(f"\nModel not found error: {error_message}", file=sys.stderr)
                print("This model may not be available. Trying again...", file=sys.stderr)
                wait_time = 30  # Fixed waiting time for entity not found errors
                time.sleep(wait_time)
                continue
                
            # Check for authentication errors
            if any(pattern in error_message.lower() for pattern in ["authentication", "unauthorized", "auth", "token", "apikey", "api key", "illegal header", "bearer"]):
                print(f"\nAuthentication error: {error_message}", file=sys.stderr)
                print("This could be due to an invalid API key. Verifying authentication...", file=sys.stderr)
                
                # Get the API key again from environment (in case it changed)
                auth_token = os.environ.get('OPENAI_API_KEY', 'Not Set')
                if auth_token == 'Not Set' or len(auth_token) < 10:
                    print("API key appears to be missing or invalid!", file=sys.stderr)
                else:
                    token_prefix = auth_token[:5]
                    token_suffix = auth_token[-5:]
                    print(f"Current API key: {token_prefix}...{token_suffix}", file=sys.stderr)
                
                # Wait a bit longer for auth errors
                wait_time = 60 + random.uniform(0, 30)
                print(f"Waiting {wait_time:.2f} seconds before retrying...", file=sys.stderr)
                time.sleep(wait_time)
                continue
            
            # Check if it's a rate limit error (look for multiple possible patterns)
            is_rate_limit = False
            if any(pattern in error_message.lower() for pattern in [
                "rate limit", "429", "too many requests", "quota exceeded", 
                "limit exceeded", "cap", "ratelimit", "limit_rpd"
            ]):
                is_rate_limit = True
            
            # If it's a rate limit error or a connection error that could benefit from retrying
            if is_rate_limit or any(pattern in error_message.lower() for pattern in [
                "connection", "timeout", "refused", "reset", "broken pipe", 
                "network", "dns", "socket", "eof", "closed"
            ]):
                # Calculate wait time with exponential backoff and jitter
                wait_time = base_wait_time * (2 ** retry_count) + random.uniform(0, 5)
                
                # Try different ways to extract reset time information
                reset_time = None
                
                # Method 1: Standard X-RateLimit-Reset header
                reset_match = re.search(r'X-RateLimit-Reset: (\d+)', error_message)
                if reset_match:
                    try:
                        reset_time = int(reset_match.group(1)) / 1000  # Convert to seconds
                    except (ValueError, TypeError):
                        pass
                
                # Method 2: OpenRouter specific format with timestamp
                if not reset_time:
                    reset_match = re.search(r'"X-RateLimit-Reset": "?(\d+)"?', error_message)
                    if reset_match:
                        try:
                            reset_time = int(reset_match.group(1)) / 1000  # Convert to seconds
                        except (ValueError, TypeError):
                            pass
                
                # Method 3: Timestamp directly in the message
                if not reset_time:
                    timestamp_match = re.search(r'(\d{10,13})', error_message)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        try:
                            # If it's milliseconds (13 digits), convert to seconds
                            if len(timestamp) >= 13:
                                reset_time = int(timestamp) / 1000
                            else:
                                reset_time = int(timestamp)
                        except (ValueError, TypeError):
                            pass
                
                # If we found a reset time, use it to calculate wait time
                if reset_time:
                    current_time = time.time()
                    if reset_time > current_time:
                        wait_time = min(reset_time - current_time + random.uniform(1, 10), 600)  # Add buffer, cap at 10 minutes
                        print(f"Rate limit will reset at timestamp {reset_time}", file=sys.stderr)
                
                # Apply model-specific multiplier to the wait time
                model_multiplier = 1.0
                for prefix, delay in MODEL_SPECIFIC_DELAYS.items():
                    if prefix in model:
                        model_multiplier = delay / base_wait_time
                        break
                
                wait_time = wait_time * model_multiplier
                
                # Cap the maximum wait time to 15 minutes to prevent very long waits
                wait_time = min(wait_time, 900)
                
                error_type = "Rate limit" if is_rate_limit else "Connection"
                print(f"\n{error_type} error encountered: {error_message}", file=sys.stderr)
                print(f"Retrying in {wait_time:.2f} seconds (Attempt {retry_count}/{MAX_RETRIES})...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                # For non-rate-limit errors, print detailed traceback
                print(f"\nError encountered (Attempt {retry_count}/{MAX_RETRIES}): {error_message}", file=sys.stderr)
                print("Error details:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                
                # For some errors (like model unavailability), add a small delay and continue
                if any(pattern in error_message.lower() for pattern in [
                    "unavailable", "no provider", "model not found", "entity not found", 
                    "internal server error", "500", "503", "502", "maintenance"
                ]):
                    wait_time = base_wait_time * (2 ** retry_count) + random.uniform(0, 5)
                    wait_time = min(wait_time, 300)  # Cap at 5 minutes for these errors
                    print(f"Service issue detected, retrying in {wait_time:.2f} seconds...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    # For other errors, still retry but with a shorter delay
                    wait_time = base_wait_time + random.uniform(1, 5) * retry_count
                    print(f"Unexpected error, retrying in {wait_time:.2f} seconds...", file=sys.stderr)
                    time.sleep(wait_time)
    
    # If we've exhausted all retries
    error_msg = f"Failed after {MAX_RETRIES} attempts."
    if last_error:
        error_msg += f" Last error: {str(last_error)}"
    raise Exception(error_msg)


def extract_json(text):
    """
    Extract JSON from text that might contain additional content.
    Tries multiple patterns to find valid JSON.
    """
    # Try to find JSON-like content within triple backticks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass  # Try other methods if this fails

    # If no triple backticks, try to find outer-most curly braces
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass  # Try other methods if this fails
    
    # Try to find anything that looks like JSON with keys and values
    # This is a more aggressive approach for malformed JSON
    json_like = {}
    
    # Look for patterns like "key": "value" or "key": number
    key_value_pattern = r'"([^"]+)"\s*:\s*(?:"([^"]*)"|\[.*?\]|(\d+)|\{.*?\}|true|false|null)'
    matches = re.findall(key_value_pattern, text, re.DOTALL)
    
    if matches:
        for match in matches:
            key = match[0]
            # Figure out which value group matched
            if match[1]:  # String value
                value = match[1]
            elif match[2]:  # Number value
                try:
                    value = int(match[2])
                except ValueError:
                    try:
                        value = float(match[2])
                    except ValueError:
                        value = match[2]  # Keep as string if can't convert
            else:
                # Could be a complex value (array, object, boolean, null)
                # Just use a placeholder for now
                value = "[complex value]"
            
            json_like[key] = value
        
        if json_like:
            print(f"Warning: Had to reconstruct JSON from text, result may be incomplete: {json_like}", file=sys.stderr)
            return json_like
    
    # If all methods fail, print the problematic text and return None
    print(f"Warning: Could not extract valid JSON from response: {text[:200]}...", file=sys.stderr)
    return None 