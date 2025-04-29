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


def generate(messages, client, model, temperature=0, top_p=1, json_format=False, reasoning=None):
    if reasoning is None:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "text"}
            if not json_format
            else {"type": "json_object"},
            top_p=top_p
        )
    else:
        if reasoning:
            reasoning_args = {
                "reasoning": {
                    "exclude": True
                }
            }
        else:
            reasoning_args = {
                "reasoning": {
                    "max_tokens": 0,
                    "exclude": True
                }
            }
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "text"}
            if not json_format
            else {"type": "json_object"},
            top_p=top_p,
            extra_body=reasoning_args,
            stream=False
        )

    if response.choices is None:
        return str(response.error)

    if json_format:
        content = response.choices[0].message.content
        # print(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # A common error is the response trying to escape speech marks, such as \' or \"
            # This is not valid JSON, so we need to remove the escape characters
            if "Invalid \\escape" in e.msg:
                print("Invalid escape character found, attempting to fix...")
                content = content.replace("\\'", "'").replace('\\"', '"')
                return json.loads(content)
            else:
                return extract_json(content)

    return response.choices[0].message.content


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
