#!/usr/bin/env python
"""
Test script for verifying the behavior of thinking variants with reasoning=none.
This script tests the base model conversion directly.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the base model conversion function
from utils.generate import get_base_model, is_thinking_variant

def test_thinking_variant_conversion():
    """Test the conversion from thinking variants to base models."""
    test_cases = [
        ("google/gemini-2.5-flash-preview:thinking", "google/gemini-2.5-flash-preview"),
        ("anthropic/claude-3.7-sonnet:thinking", "anthropic/claude-3.7-sonnet"),
        ("google/gemini-2.5-flash-preview", "google/gemini-2.5-flash-preview"),  # No change
        ("openai/o1", "openai/o1"),  # No change
    ]
    
    for input_model, expected_output in test_cases:
        output = get_base_model(input_model)
        assert output == expected_output, f"Expected {expected_output} but got {output} for {input_model}"
        print(f"✓ {input_model} -> {output}")
    
    print("All base model conversion tests passed!")

def test_is_thinking_variant():
    """Test the is_thinking_variant function."""
    test_cases = [
        ("google/gemini-2.5-flash-preview:thinking", True),
        ("anthropic/claude-3.7-sonnet:thinking", True),
        ("google/gemini-2.5-flash-preview", False),
        ("openai/o1", False),
    ]
    
    for input_model, expected_output in test_cases:
        output = is_thinking_variant(input_model)
        assert output == expected_output, f"Expected {expected_output} but got {output} for {input_model}"
        print(f"✓ is_thinking_variant({input_model}) -> {output}")
    
    print("All is_thinking_variant tests passed!")

if __name__ == "__main__":
    print("Testing thinking variant conversion...")
    test_thinking_variant_conversion()
    
    print("\nTesting is_thinking_variant function...")
    test_is_thinking_variant()
    
    print("\nAll tests passed! The implementation should correctly convert thinking variants to base models when reasoning=none.") 