#!/usr/bin/env python3
"""
Script to patch run.py to better handle Claude reasoning extraction
"""

import os
import re
from utils.run_claude_fix import extract_reasoning_content, get_reasoning_tokens, extract_data_for_output

def patch_run_py():
    """
    Apply changes to run.py to properly handle Claude model reasoning extraction.
    This creates a backup and then modifies the file.
    """
    # Paths
    run_py_path = "utils/run.py"
    backup_path = "utils/run.py.bak"
    
    # Create backup
    if not os.path.exists(backup_path):
        print(f"Creating backup of {run_py_path} to {backup_path}")
        with open(run_py_path, 'r') as f_in:
            content = f_in.read()
        
        with open(backup_path, 'w') as f_out:
            f_out.write(content)
    else:
        print(f"Backup already exists at {backup_path}")
        with open(run_py_path, 'r') as f_in:
            content = f_in.read()
    
    # Pattern 1: Add imports for the new functions
    import_pattern = r'import json\nfrom utils import \(\n'
    if 'from utils.run_claude_fix' not in content:
        import_replacement = 'import json\nfrom utils.run_claude_fix import extract_reasoning_content, get_reasoning_tokens\nfrom utils import (\n'
        content = re.sub(import_pattern, import_replacement, content)
        print("Added import for reasoning extraction functions")
    
    # Pattern 2: Replace the direct extraction logic with our enhanced version
    # Find the reasoning extraction block
    extraction_pattern = r'# Extract and save reasoning content immediately to prevent loss\s+reasoning_content = None\s+.*?# Check if response has reasoning as an attribute.*?if response.*?}'
    
    # New extraction code
    extraction_replacement = '''# Extract and save reasoning content immediately to prevent loss
        reasoning_content = extract_reasoning_content(response, target_model)
        if reasoning_content:
            print(f"DEBUG: Successfully extracted reasoning content, length={len(str(reasoning_content))}")
        else:
            print(f"DEBUG: No reasoning content found in response")'''
    
    # Use re.DOTALL to match across lines
    content = re.sub(extraction_pattern, extraction_replacement, content, flags=re.DOTALL)
    print("Updated reasoning extraction logic")
    
    # Pattern 3: Replace the token usage building block to use enhanced reasoning token extraction
    # Find the token usage related code
    token_pattern = r'if target_token_usage and "reasoning_tokens" in target_token_usage.*?print\(f"DEBUG: Set reasoning=True based on reasoning_tokens={target_token_usage.*?}".*?\)'
    
    # New token usage code with enhanced reasoning token extraction
    token_replacement = '''# Use our enhanced reasoning token extraction
                if reasoning_content:
                    output_data["reasoning"] = True
                    print(f"DEBUG: Set reasoning=True based on detected reasoning content")
                    
                    # Get or estimate reasoning tokens
                    reasoning_tokens = get_reasoning_tokens(response, target_model)
                    if reasoning_tokens > 0 and target_token_usage:
                        target_token_usage["reasoning_tokens"] = reasoning_tokens
                        print(f"DEBUG: Updated reasoning_tokens in token_usage to {reasoning_tokens}")'''
    
    # Use re.DOTALL to match across lines
    content = re.sub(token_pattern, token_replacement, content, flags=re.DOTALL)
    print("Updated token usage and reasoning tokens logic")
    
    # Save the updated file
    with open(run_py_path, 'w') as f_out:
        f_out.write(content)
    
    print(f"Successfully patched {run_py_path}")

def print_usage():
    """Print usage instructions."""
    print("""
Fix Claude Reasoning Script
---------------------------
This script patches run.py to better handle reasoning extraction from Claude models.

Usage:
    python fix_claude_reasoning.py

The script will:
1. Create a backup of utils/run.py at utils/run.py.bak (if it doesn't exist)
2. Update the reasoning extraction logic to handle Claude-specific formats
3. Enhance the token usage calculation for reasoning

To test Claude reasoning:
    python debug_claude_reasoning.py
""")

if __name__ == "__main__":
    print_usage()
    try:
        patch_run_py()
        print("\nSuccessfully fixed Claude reasoning extraction in run.py!")
        print("You can now test it by running:")
        print("    python debug_claude_reasoning.py")
    except Exception as e:
        print(f"Error fixing run.py: {str(e)}") 