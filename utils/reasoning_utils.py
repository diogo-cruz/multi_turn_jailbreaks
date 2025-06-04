import re
import json

def extract_reasoning_content(response, model_name=""):
    """
    Extract reasoning content from various model responses, with specific handling for Claude.
    
    Parameters:
    - response: The response object or text from the model
    - model_name: Optional model name for specialized handling
    
    Returns:
    - reasoning_content: The extracted reasoning content or None if not found
    """
    reasoning_content = None
    model_name = model_name.lower() if model_name else ""
    
    # TODO: remove debug prints
    # Debug information
    print(f"DEBUG: Extracting reasoning from response type: {type(response)}")
    
    # Case 1: Response is a dictionary with reasoning field
    if isinstance(response, dict) and "reasoning" in response:
        reasoning_content = response.get("reasoning")
        print(f"DEBUG: Extracted reasoning from response dict field 'reasoning', len={len(str(reasoning_content)) if reasoning_content else 0}")
        return reasoning_content
        
    # Case 2: Response has reasoning as an attribute (most OpenRouter models)
    if hasattr(response, "reasoning"):
        reasoning_content = getattr(response, "reasoning")
        print(f"DEBUG: Extracted reasoning from response object attribute 'reasoning', len={len(str(reasoning_content)) if reasoning_content else 0}")
        return reasoning_content
        
    # Case 3: Response has thinking as an attribute (some models like Claude)
    if hasattr(response, "thinking"):
        reasoning_content = getattr(response, "thinking")
        print(f"DEBUG: Extracted reasoning from response object attribute 'thinking', len={len(str(reasoning_content)) if reasoning_content else 0}")
        return reasoning_content
        
    # Case 4: For Claude models, check for specific fields in the response object
    if "claude" in model_name:
        # Case 4a: Claude might have a message object with a reasoning field
        if hasattr(response, "choices") and response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            
            # Look for various reasoning attribute names Claude might use
            for attr_name in ["reasoning", "thinking", "internal_monologue", "chain_of_thought"]:
                if hasattr(message, attr_name):
                    reasoning_content = getattr(message, attr_name)
                    print(f"DEBUG: Extracted Claude reasoning from message.{attr_name}, len={len(str(reasoning_content)) if reasoning_content else 0}")
                    return reasoning_content
                    
            # Some models might return custom JSON in the content field with reasoning
            if hasattr(message, "content"):
                content = message.content
                
                # Try to find reasoning in JSON format within the content
                try:
                    # Check if the content is valid JSON
                    if content.strip().startswith("{") and content.strip().endswith("}"):
                        content_json = json.loads(content)
                        if "reasoning" in content_json:
                            reasoning_content = content_json["reasoning"]
                            print(f"DEBUG: Extracted reasoning from JSON content, len={len(str(reasoning_content)) if reasoning_content else 0}")
                            return reasoning_content
                except:
                    pass  # Not JSON, continue with other methods
    
    # Case 5: For Qwen models that use <thinking> tags in content
    if isinstance(response, str):
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', response, re.DOTALL)
        if thinking_match:
            reasoning_content = thinking_match.group(1)
            print(f"DEBUG: Extracted reasoning from <thinking> tags in string, len={len(reasoning_content)}")
            return reasoning_content
    elif hasattr(response, "choices") and response.choices and len(response.choices) > 0:
        # Check if content contains Qwen's <thinking> tags
        if hasattr(response.choices[0].message, "content"):
            content = response.choices[0].message.content
            thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
            if thinking_match:
                reasoning_content = thinking_match.group(1)
                print(f"DEBUG: Extracted reasoning from <thinking> tags in message content, len={len(reasoning_content)}")
                return reasoning_content
    
    # Case 6: Models that use JSON structure in content with reasoning field
    if hasattr(response, "choices") and response.choices and len(response.choices) > 0:
        if hasattr(response.choices[0].message, "content"):
            content = response.choices[0].message.content
            try:
                # Try to parse content as JSON if it appears to be JSON
                if content.strip().startswith("{") and content.strip().endswith("}"):
                    content_json = json.loads(content)
                    if "reasoning" in content_json:
                        reasoning_content = content_json["reasoning"]
                        print(f"DEBUG: Extracted reasoning from JSON content structure, len={len(str(reasoning_content))}")
                        return reasoning_content
            except:
                pass  # Not valid JSON, continue
    
    # No reasoning found
    print("DEBUG: No reasoning content found in response")
    return None

def get_reasoning_tokens(response, model_name=""):
    """
    Extract reasoning token count from response usage data.
    
    Parameters:
    - response: The response object from the model
    - model_name: Optional model name for specialized handling
    
    Returns:
    - reasoning_tokens: The number of reasoning tokens or 0 if not found
    """
    reasoning_tokens = 0
    
    # Case 1: Response has usage attribute with completion_tokens_details
    if hasattr(response, "usage"):
        usage = response.usage
        
        # Check for completion_tokens_details with reasoning_tokens field
        if hasattr(usage, "completion_tokens_details"):
            details = usage.completion_tokens_details
            if hasattr(details, "reasoning_tokens"):
                reasoning_tokens = details.reasoning_tokens
                print(f"DEBUG: Found reasoning_tokens in completion_tokens_details: {reasoning_tokens}")
                return reasoning_tokens
    
    # Case 2: If we have a dict with token_usage
    if isinstance(response, dict) and "token_usage" in response:
        token_usage = response["token_usage"]
        if "reasoning_tokens" in token_usage:
            reasoning_tokens = token_usage["reasoning_tokens"]
            print(f"DEBUG: Found reasoning_tokens in token_usage dict: {reasoning_tokens}")
            return reasoning_tokens
    
    # Case 3: Estimate tokens from reasoning content
    reasoning_content = extract_reasoning_content(response, model_name)
    if reasoning_content:
        # Rough approximation of tokens based on string length
        estimated_tokens = len(str(reasoning_content)) // 4  # ~4 chars per token on average
        print(f"DEBUG: Estimated reasoning tokens from content length: ~{estimated_tokens}")
        return estimated_tokens
    
    return reasoning_tokens

# Example of how to improve the data extraction in run.py
def extract_data_for_output(response, target_model):
    """
    Extract and prepare data for the output file in a consistent format.
    
    Parameters:
    - response: The response from the model
    - target_model: The name of the target model
    
    Returns:
    - dict containing extracted data with reasoning content and token usage
    """
    # Basic output structure
    output_data = {
        "reasoning": False,  # Will be set to True if reasoning content is found
    }
    
    # Extract response content
    if isinstance(response, dict) and "content" in response:
        output_data["target_response"] = response["content"]
    elif hasattr(response, "content"):
        output_data["target_response"] = response.content
    elif hasattr(response, "choices") and response.choices and hasattr(response.choices[0].message, "content"):
        output_data["target_response"] = response.choices[0].message.content
    else:
        output_data["target_response"] = str(response)
    
    # Extract and clean Qwen responses with <thinking> tags
    if isinstance(output_data["target_response"], str) and "<thinking>" in output_data["target_response"]:
        # Remove thinking tags from visible response
        output_data["target_response"] = re.sub(r'<thinking>.*?</thinking>', '', output_data["target_response"], flags=re.DOTALL)
    
    # Extract token usage information
    token_usage = {}
    if hasattr(response, "usage"):
        token_usage = {
            "available": True,
            "model": target_model,
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
            "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }
        
        # Add reasoning tokens if available
        reasoning_tokens = get_reasoning_tokens(response, target_model)
        if reasoning_tokens > 0:
            token_usage["reasoning_tokens"] = reasoning_tokens
    
    # Add token usage to output if available
    if token_usage:
        output_data["token_usage"] = token_usage
    
    # Extract reasoning content - this is critical for the issue
    reasoning_content = extract_reasoning_content(response, target_model)
    if reasoning_content:
        output_data["reasoning_content"] = reasoning_content
        output_data["reasoning"] = True
        
        # If we have reasoning content but no token usage data, create estimated data
        if "token_usage" not in output_data:
            estimated_tokens = len(str(reasoning_content)) // 4
            output_data["token_usage"] = {
                "available": True,
                "model": target_model,
                "reasoning_tokens": estimated_tokens,
                "prompt_tokens": 0,  # Unknown
                "completion_tokens": len(output_data["target_response"]) // 4,  # Rough estimation
                "total_tokens": (len(output_data["target_response"]) + len(str(reasoning_content))) // 4  # Rough estimation
            }
    
    return output_data 