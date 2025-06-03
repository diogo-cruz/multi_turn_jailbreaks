#!/usr/bin/env python3
"""
Model matching utilities for plotting scripts.
Uses flexible matching without hardcoded data.
"""

import pandas as pd
import numpy as np

def extract_model_family(model_name):
    """Extract model family from model name"""
    model_lower = model_name.lower()
    
    if 'deepseek' in model_lower:
        return 'DeepSeek'
    elif 'claude' in model_lower or 'anthropic' in model_lower:
        return 'Anthropic'
    elif 'gemini' in model_lower or 'gemma' in model_lower:
        return 'Google'
    elif 'llama' in model_lower or 'meta' in model_lower:
        return 'Meta'
    elif 'mistral' in model_lower:
        return 'Mistral'
    elif 'qwen' in model_lower:
        return 'Qwen'
    elif 'gpt' in model_lower or 'openai' in model_lower or 'o1' in model_lower or 'o3' in model_lower or 'o4' in model_lower:
        return 'OpenAI'
    elif 'grok' in model_lower or 'x-ai' in model_lower:
        return 'xAI'
    else:
        return 'Other'

def create_model_mapping(model_info_df):
    """
    Create a mapping from experimental model names to model info using flexible matching.
    
    Args:
        model_info_df: DataFrame with model comparison data
    
    Returns:
        dict: Mapping from experimental model name to model info row
    """
    # Create a lookup dictionary for model info
    model_lookup = {}
    for _, row in model_info_df.iterrows():
        model_lookup[row['Model']] = row
    
    def find_best_match(exp_model_name):
        """Find the best matching model info for an experimental model name"""
        exp_lower = exp_model_name.lower()
        
        # First try exact match
        if exp_model_name in model_lookup:
            return model_lookup[exp_model_name]
        
        # Try case-insensitive exact match
        for model_name in model_lookup.keys():
            if model_name.lower() == exp_lower:
                return model_lookup[model_name]
        
        # Try partial matching - look for models that contain key parts
        best_match = None
        best_score = 0
        
        for model_name in model_lookup.keys():
            model_lower = model_name.lower()
            score = 0
            
            # Check for common substrings
            exp_parts = exp_lower.replace('/', ' ').replace('-', ' ').split()
            model_parts = model_lower.replace('/', ' ').replace('-', ' ').split()
            
            # Count matching parts
            for exp_part in exp_parts:
                if len(exp_part) > 2:  # Only consider meaningful parts
                    for model_part in model_parts:
                        if exp_part in model_part or model_part in exp_part:
                            score += 1
            
            # Boost score if model families match
            exp_family = extract_model_family(exp_model_name).lower()
            model_family = extract_model_family(model_name).lower()
            if exp_family == model_family and exp_family != 'other':
                score += 3
            
            if score > best_score:
                best_score = score
                best_match = model_lookup[model_name]
        
        return best_match if best_score > 1 else None
    
    return find_best_match

def get_model_data_with_info(asr_data, model_info_df, required_columns):
    """
    Merge ASR data with model information.
    
    Args:
        asr_data: DataFrame with ASR results
        model_info_df: DataFrame with model comparison data  
        required_columns: List of required columns from model info
    
    Returns:
        list: List of dictionaries with merged data
    """
    matcher = create_model_mapping(model_info_df)
    merged_data = []
    matched_count = 0
    total_count = len(asr_data)
    
    for _, row in asr_data.iterrows():
        model_info = matcher(row['target_model'])
        
        if model_info is not None:
            # Check if all required columns are available and not null
            has_required_data = True
            for col in required_columns:
                if col not in model_info or pd.isna(model_info[col]):
                    has_required_data = False
                    break
            
            if has_required_data:
                merged_row = {
                    'model': row['target_model'],
                    'turn_type': row['turn_type'],
                    'asr': row['goal_achieved'],
                    'family': extract_model_family(row['target_model'])
                }
                
                # Add model info columns
                for col in required_columns:
                    merged_row[col.lower().replace(' ', '_')] = model_info[col]
                
                merged_data.append(merged_row)
                matched_count += 1
    
    print(f"Model matching: {matched_count}/{total_count} ({100*matched_count/total_count:.1f}%) models matched with required data")
    
    if matched_count < total_count:
        print(f"Note: {total_count - matched_count} models missing from model_comparison.csv or lacking required data")
        print("See human_TODO.md for details on missing models")
    
    return merged_data 