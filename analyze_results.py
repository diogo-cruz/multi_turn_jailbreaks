import os
import re
import json
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

def extract_score(content, pattern, warning_counter=None):
    """Extract a score from the content using flexible pattern matching."""
    if warning_counter is None:
        warning_counter = {'count': 0}
        
    # List of score formats to try
    formats = [
        # Standard format with optional scale and trailing content
        pattern + r'[^\n]*?:\s*(\d+(?:\.\d+)?)\s*(?:/[5|100])?\s*(?:\n|$)',
        # Format for scores at end of line
        pattern + r'[^\n]*?:\s*.*?(\d+(?:\.\d+)?)/[5|100]\s*$',
        # Format for scores in parentheses
        pattern + r'[^\n]*?:\s*.*?\((\d+(?:\.\d+)?)\)',
        # Format with "Score:" prefix
        pattern + r'[^\n]*Score:\s*(\d+(?:\.\d+)?)',
        # Format for score ranges
        pattern + r'[^\n]*?:\s*.*?(\d+(?:\.\d+)?)\s*-\s*\d+',
        # Format with descriptive text between field and score
        pattern + r'[^\n]*?:.*?(\d+(?:\.\d+)?)\s*(?:/[5|100])?\s*(?:\n|$)',
        # Format for scores embedded in text
        pattern + r'[^\n]*?:\s*.*?(\d+(?:\.\d+)?)\s*(?:/[5|100])?\s*[^\n]*',
        # Extremely flexible pattern as last resort
        pattern + r'.*?(\d+(?:\.\d+)?)\s*(?:/[5|100])?\s*(?:\n|$)'
    ]
    
    # N/A patterns to check first
    na_patterns = [
        pattern + r'[^\n]*?:\s*(?:N/A|NA|None|-)\s*(?:\n|$)',
        pattern + r'[^\n]*?:\s*.*?\((?:N/A|NA|None|-)\)',
        r'[^\n]*?:\s*.*?(?:N/A|NA|None|-)\s*$'
    ]
    
    # Check for N/A first
    for na_pattern in na_patterns:
        if re.search(na_pattern, content, re.IGNORECASE | re.MULTILINE):
            return None
            
    # Try each format
    for fmt in formats:
        match = re.search(fmt, content, re.MULTILINE)
        if match:
            try:
                score = float(match.group(1))
                # Validate score is in reasonable range
                if 0 <= score <= 100:
                    return score
            except (ValueError, IndexError):
                continue
    
    # If no match found in any format, increment warning counter
    if warning_counter is not None:
        warning_counter['count'] += 1
    
    # Last resort: try to find any number after the pattern
    last_resort = re.search(pattern + r'[^\n]*?(\d+(?:\.\d+)?)', content)
    if last_resort:
        try:
            score = float(last_resort.group(1))
            if 0 <= score <= 100:
                return score
        except (ValueError, IndexError):
            pass
    
    return None

def extract_round_scores(jsonl_path: Path) -> Tuple[List[int], bool, int]:
    """Extract scores for each round and goal achievement status from JSONL file"""
    try:
        scores = []
        goal_achieved = False
        with open(jsonl_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'round' in data and 'score' in data:
                        try:
                            score = data['score']
                            if isinstance(score, (int, float)):
                                scores.append(int(score))
                            elif isinstance(score, str):
                                # Try to convert string score to int, handling both "9" and "9/10" formats
                                score = score.split('/')[0].strip()
                                if score.isdigit():
                                    scores.append(int(score))
                                else:
                                    scores.append(None)
                            else:
                                scores.append(None)
                        except (ValueError, AttributeError):
                            scores.append(None)
                    elif 'goal_achieved' in data:
                        goal_achieved = bool(data['goal_achieved'])
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON line in {jsonl_path}")
                    continue
        
        valid_scores = [s for s in scores if s is not None]
        return scores, goal_achieved, len(valid_scores)
    except Exception as e:
        print(f"Error reading round scores from {jsonl_path}: {str(e)}")
        return [], False, 0

def extract_jsonl_metadata(jsonl_path: Path) -> Dict:
    """Extract metadata from JSONL file"""
    metadata = {}
    try:
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
            if not lines:
                print(f"WARNING: Empty JSONL file: {jsonl_path}")
                return metadata
                
            try:
                # Extract metadata from first line
                first_line = lines[0].strip()
                data = json.loads(first_line)
                metadata['target_model'] = data.get('target_model', None)
                metadata['attacker_model'] = data.get('attacker_model', None)
                metadata['test_case'] = data.get('test_case', None)
                
                # Process all lines for round information
                round_scores = []
                completed_rounds = 0
                goal_achieved = False
                
                for line in lines:
                    try:
                        round_data = json.loads(line.strip())
                        
                        # Check for goal achievement in any round
                        if round_data.get('goal_achieved', False):
                            goal_achieved = True
                        
                        # Extract score if present
                        if 'score' in round_data:
                            score = round_data['score']
                            # Handle both numeric and string scores
                            if isinstance(score, (int, float)):
                                round_scores.append(float(score))
                            elif isinstance(score, str):
                                # Handle "N/A" scores
                                if score.lower() in ['n/a', 'na']:
                                    round_scores.append(None)
                                # Handle "X/Y" format
                                elif '/' in score:
                                    num = float(score.split('/')[0])
                                    round_scores.append(num)
                                # Handle plain numbers as strings
                                elif score.replace('.','',1).isdigit():
                                    round_scores.append(float(score))
                            completed_rounds += 1
                            
                    except json.JSONDecodeError:
                        continue
                
                # Update metadata with round information
                metadata['goal_achieved'] = goal_achieved
                metadata['completed_rounds'] = completed_rounds
                
                # Calculate round score statistics if we have valid scores
                valid_scores = [s for s in round_scores if s is not None]
                if valid_scores:
                    metadata['round_scores'] = round_scores
                    metadata['average_round_score'] = float(np.mean(valid_scores))
                    metadata['max_round_score'] = float(np.max(valid_scores))
                else:
                    metadata['round_scores'] = None
                    metadata['average_round_score'] = None
                    metadata['max_round_score'] = None
                    
            except json.JSONDecodeError as e:
                print(f"WARNING: Invalid JSON in first line of {jsonl_path}: {str(e)}")
                
    except Exception as e:
        print(f"ERROR reading JSONL file {jsonl_path}: {str(e)}")
        
    return metadata

def standardize_test_case_type(test_type: str) -> str:
    """Standardize test case type formatting"""
    if not test_type:
        return "unknown"
    return test_type.lower().strip()

def extract_primary_issues(content):
    """Extract primary issues from the content using flexible pattern matching."""
    # Try multiple section header patterns
    section_patterns = [
        r'Primary Issues(?:\s+Identified)?:(.+?)(?=(?:Secondary|Additional|Other)\s+Issues:|###|\n\s*\n|$)',
        r'(?:Key|Main|Critical)\s+Issues:(.+?)(?=###|\n\s*\n|$)',
        r'Issues(?:\s+Found)?:(.+?)(?=###|\n\s*\n|$)',
        r'Problems(?:\s+Identified)?:(.+?)(?=###|\n\s*\n|$)',
        r'Areas for Improvement:(.+?)(?=##|\n\s*\n|$)',
        r'Areas for Improvement:(.+?)(?=\d\.|##|\n\s*\n|$)',
        r'(?:^|\n)\s*-\s*\*\*Areas for Improvement\*\*:(.+?)(?=##|\n\s*\n|$)',
        r'(?:^|\n)## .*?\n.*?Areas for Improvement:(.+?)(?=##|\n\s*\n|$)',
        r'(?:^|\n)## Response Quality Assessment\n.*?Areas for Improvement:(.+?)(?=##|\n\s*\n|$)',
        r'(?:^|\n)## .*?Assessment\n.*?Areas for Improvement:(.+?)(?=##|\n\s*\n|$)',
        r'(?:^|\n)## .*?Assessment\n.*?(?:Key|Main|Critical)\s+Issues:(.+?)(?=##|\n\s*\n|$)',
        r'(?:^|\n)## .*?Assessment\n.*?(?:Areas|Points) to (?:Improve|Address):(.+?)(?=##|\n\s*\n|$)'
    ]
    
    # Find all Areas for Improvement sections
    all_sections = []
    for pattern in section_patterns:
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            section_text = match.group(1).strip()
            if section_text:
                all_sections.append(section_text)
    
    if not all_sections:
        # Try looking in each section
        section_pattern = r'##[^#].*?\n(.*?)(?=##|\Z)'
        matches = re.finditer(section_pattern, content, re.DOTALL)
        for match in matches:
            section_text = match.group(1)
            # Look for issues within this section
            for pattern in section_patterns:
                submatch = re.search(pattern, section_text, re.DOTALL | re.IGNORECASE)
                if submatch:
                    section_text = submatch.group(1).strip()
                    if section_text:
                        all_sections.append(section_text)
    
    if not all_sections:
        return []
        
    # Multiple item patterns to try
    item_patterns = [
        # Numbered items with optional period or parenthesis
        r'(?:^|\n)\s*\d+\.?\)?\s*(.+?)(?=(?:\n\s*\d+\.?\)?|$))',
        # Bullet points with various markers
        r'(?:^|\n)\s*[-*•]\s*(.+?)(?=(?:\n\s*[-*•]|$))',
        # Labeled items
        r'(?:^|\n)\s*[A-Z][A-Za-z\s]+:\s*(.+?)(?=(?:\n\s*[A-Z]|$))',
        # Dash-prefixed items
        r'(?:^|\n)\s*-\s*(.+?)(?=(?:\n\s*-|$))',
        # Items in a list after a colon
        r'(?:^|\n)\s*\d+\.\s*(.+?)(?=(?:\n\s*\d+\.|$))',
        # Items with Could/May prefix
        r'(?:^|\n)\s*(?:Could|May)\s+(.+?)(?=\n|$)',
        # Items with asterisk prefix
        r'(?:^|\n)\s*\*\s*(.+?)(?=(?:\n\s*\*|$))',
        # Fallback pattern for any line
        r'(?:^|\n)\s*(.+?)(?=\n|$)'
    ]
    
    issues = []
    for section_text in all_sections:
        for pattern in item_patterns:
            matches = re.finditer(pattern, section_text)
            for match in matches:
                issue = match.group(1).strip()
                # Clean up the issue text
                issue = re.sub(r'^\s*[-*•\d.)\s]+\s*', '', issue)
                issue = issue.strip()
                # Filter out empty or too short issues
                if issue and len(issue) > 5:
                    # Skip if starts with certain prefixes
                    if not re.match(r'^(?:note:|nb:|summary:|strengths?:|could\s+|may\s+)', issue.lower()):
                        issues.append(issue)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_issues = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique_issues.append(issue)
    
    return unique_issues

def categorize_issues(issues: List[str]) -> Dict[str, bool]:
    """Categorize issues based on predefined problem categories and sub-categories"""
    categories = {
        # Scoring Metric Issues
        'scoring_metric_issues': False,
        'scoring_rubric_inconsistency': False,  # Dynamic rubric generation issues
        'scoring_false_positives': False,       # False positive detection problems
        'scoring_length_bias': False,           # Length-based scoring bias
        
        # Model Response Issues
        'model_response_issues': False,
        'response_hallucination': False,        # Heavy hallucination
        'response_nonsensical': False,          # Nonsensical outputs
        'response_incoherent': False,           # Incoherent responses
        
        # Attacker Model Issues
        'attacker_model_issues': False,
        'attacker_refusal': False,              # GPT-4 refusing to generate prompts
        'attacker_inefficient': False,          # Inefficient attack strategies
        'attacker_random': False,               # Random/unfocused attempts
        
        # Test Case Definition Issues
        'test_case_definition_issues': False,
        'definition_vague': False,              # Vague success criteria
        'definition_ambiguous': False,          # Ambiguous objectives
        'definition_unclear': False,            # Unclear system prompts
        
        # Technical Implementation Issues
        'technical_implementation_issues': False,
        'implementation_refusal': False,        # Handling model refusals
        'implementation_conversation': False,    # Conversation tracking issues
        'implementation_rounds': False          # Round management problems
    }
    
    keywords = {
        # Scoring Metric Issues
        'scoring_rubric_inconsistency': [
            'rubric', 'scoring criteria', 'evaluation criteria', 'inconsistent', 
            'scoring system', 'scoring shows', 'criteria appears', 'variation in strictness'
        ],
        'scoring_false_positives': [
            'false positive', 'misclassified', 'misidentified', 'wrong classification',
            'vulnerability to false', 'potentially misclassified'
        ],
        'scoring_length_bias': [
            'length bias', 'response length', 'lengthy response', 'long output',
            'focus on content rather than length'
        ],
        
        # Model Response Issues
        'response_hallucination': [
            'hallucination', 'fabricated', 'made up', 'invented', 'speculative',
            'unverified information'
        ],
        'response_nonsensical': [
            'nonsensical', 'gibberish', 'meaningless', 'illogical', 'incoherent output'
        ],
        'response_incoherent': [
            'incoherent', 'inconsistent response', 'unclear response', 'confused',
            'poorly structured'
        ],
        
        # Attacker Model Issues
        'attacker_refusal': [
            'refuses to generate', 'attacker refusal', 'gpt-4 refuses', 'won\'t generate',
            'limited success', 'ineffective against'
        ],
        'attacker_inefficient': [
            'inefficient attack', 'ineffective strategy', 'poor attack', 'limited sophistication',
            'straightforward attempts', 'basic approach'
        ],
        'attacker_random': [
            'random attempts', 'unfocused', 'scattered approach', 'lacks sophistication',
            'without sophisticated'
        ],
        
        # Test Case Definition Issues
        'definition_vague': [
            'vague criteria', 'unclear criteria', 'undefined success', 'unclear standards',
            'needs clearer definition'
        ],
        'definition_ambiguous': [
            'ambiguous', 'unclear objective', 'unclear goal', 'multiple interpretations'
        ],
        'definition_unclear': [
            'unclear prompt', 'unclear system', 'unclear instruction', 'needs better specification'
        ],
        
        # Technical Implementation Issues
        'implementation_refusal': [
            'handling refusal', 'model refusal', 'rejection handling', 'error handling',
            'handling of model refusals'
        ],
        'implementation_conversation': [
            'conversation tracking', 'dialogue management', 'turn tracking',
            'tracking of interactions'
        ],
        'implementation_rounds': [
            'round management', 'turn counting', 'conversation rounds',
            'tracking rounds'
        ]
    }
    
    # Process each issue
    for issue in issues:
        issue_lower = issue.lower()
        
        # Check each keyword set
        for category, terms in keywords.items():
            if any(term.lower() in issue_lower for term in terms):
                categories[category] = True
                
                # Set parent category
                if category.startswith('scoring_'):
                    categories['scoring_metric_issues'] = True
                elif category.startswith('response_'):
                    categories['model_response_issues'] = True
                elif category.startswith('attacker_'):
                    categories['attacker_model_issues'] = True
                elif category.startswith('definition_'):
                    categories['test_case_definition_issues'] = True
                elif category.startswith('implementation_'):
                    categories['technical_implementation_issues'] = True
    
    return categories

def standardize_model_name(model_name: str) -> str:
    """Standardize model names, particularly for gpt-4o-mini"""
    if not model_name:
        return None
    
    if model_name.lower() == "gpt-4o-mini":
        print(f"INFO: Standardizing model name from 'gpt-4o-mini' to 'gpt-4o-mini-2024-07-18'")
        return "gpt-4o-mini-2024-07-18"
    return model_name

def extract_timestamp(filename: str) -> Optional[str]:
    """Extract timestamp from filename"""
    # Pattern matches YYYY_MM_DD_HH_MM_SS
    match = re.search(r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', filename)
    if match:
        return match.group(1)
    return None

def validate_required_fields(data: Dict, file_path: str, warning_counter: Dict) -> None:
    """Validate that all required fields are present and raise issues for missing fields"""
    required_fields = [
        'file_name', 'test_case_type', 'target_behavior', 'reliability_score',
        'scoring_quality', 'response_quality', 'attack_quality', 'technical_quality',
        'rubric_consistency', 'false_positive_detection', 'response_length_bias',
        'coherence', 'hallucination_level', 'task_relevance', 'attack_effectiveness',
        'strategy_progression', 'prompt_creativity', 'conversation_tracking',
        'error_handling', 'response_processing', 'target_model', 'attacker_model',
        'test_case', 'jailbreak_tactic', 'max_rounds', 'turn_type', 'target_system',
        'task', 'goal_achieved', 'completed_rounds', 'average_round_score',
        'max_round_score', 'round_scores', 'timestamp'
    ]
    
    boolean_fields = [
        'goal_achieved', 'scoring_metric_issues', 'model_response_issues', 
        'attacker_model_issues', 'technical_implementation_issues'
    ]
    
    # Initialize boolean fields to False if missing
    for field in boolean_fields:
        if field not in data or data[field] is None:
            data[field] = False
            print(f"WARNING: Initializing missing boolean field '{field}' to False in {file_path}")
            warning_counter['count'] += 1
    
    # For single-turn cases, strategy_progression should be None
    if data.get('test_case_type') == 'single-turn' and 'strategy_progression' in required_fields:
        required_fields.remove('strategy_progression')
    
    # For single-turn cases, set appropriate defaults for round-related fields
    if data.get('test_case_type') == 'single-turn':
        round_fields = {
            'completed_rounds': 1,
            'round_scores': [None],
            'average_round_score': None,
            'max_round_score': None
        }
        for field, default_value in round_fields.items():
            if field not in data or data[field] is None:
                data[field] = default_value
    
    for field in required_fields:
        if field not in data or data[field] is None:
            print(f"WARNING: Missing required field '{field}' in file {file_path}")
            warning_counter['count'] += 1

def parse_analysis_file(file_path: str, warning_counter=None) -> Dict[str, Any]:
    """Parse an analysis markdown file and extract relevant metrics."""
    if warning_counter is None:
        warning_counter = {'count': 0, 'details': []}
        
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            
        # Skip empty files
        if not content:
            warning_counter['count'] += 1
            warning_counter['details'].append(f"Empty file: {file_path}")
            return {}
            
    except Exception as e:
        warning_counter['count'] += 1
        warning_counter['details'].append(f"ERROR reading file {file_path}: {str(e)}")
        return {}

    # Define metadata patterns with variations
    metadata_patterns = {
        'file_name': [
            r'File\s*Name:?\s*([^.\n]+\.jsonl)',
            r'Analysis\s+of:?\s*([^.\n]+\.jsonl)',
            r'Analyzing:?\s*([^.\n]+\.jsonl)',
            r'Test\s+File:?\s*([^.\n]+\.jsonl)',
            r'#\s*([^#\n]+?)(?:\s+Test)?\s+Analysis',  # Match title pattern
            r'File\s*Name:?\s*([^\n]+)',  # Fallback pattern for any file name
            r'#\s*([^#\n]+)'  # Extract from title
        ],
        'test_case_type': [
            r'Test\s+Case\s+Type:?\s*([^\n]+)',
            r'Type:?\s*([^\n]+)',
            r'(?:Interaction|Test)\s+Type:?\s*([^\n]+)',
            r'(?:single|multi)[-\s]turn',  # Fallback pattern
            r'_(?:single|multi)_turn'  # Extract from filename
        ],
        'target_behavior': [
            r'Target\s+Behavior:?\s*([^\n]+)',
            r'Behavior:?\s*([^\n]+)',
            r'(?:Objective|Task):?\s*([^\n]+)',
            r'(?:Attempted\s+)?Behavior:?\s*([^\n]+)',
            r'#\s*[^#\n]+?\s+([^#\n]+?)\s+Test\s+Analysis',  # Extract from title
            r'Get\s+AI\s+to\s+([^\n]+)',  # Common format in some files
            r'#\s*([^#\n]+?)\s+Test'  # Extract from title
        ]
    }

    # Extract metadata using patterns
    metadata = {}
    for field, patterns in metadata_patterns.items():
        field_found = False
        for pattern in patterns:
            try:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value and not value.lower() in ['n/a', 'na', 'none', '-']:
                        metadata[field] = value
                        field_found = True
                        break
            except (IndexError, AttributeError):
                continue
        
        if not field_found:
            # Try to derive from file path
            if field == 'file_name':
                metadata[field] = os.path.basename(str(file_path)).replace('_analysis.md', '.jsonl')
            elif field == 'test_case_type':
                metadata[field] = 'single-turn' if 'single_turn' in str(file_path) else 'multi-turn'
            elif field == 'target_behavior':
                behavior_match = re.search(r'_([^_]+)_(?:single|multi)_turn', str(file_path))
                if behavior_match:
                    metadata[field] = behavior_match.group(1).replace('_', ' ')
                else:
                    metadata[field] = 'unknown'

    # Extract timestamp from filename
    try:
        timestamp_match = re.search(r'_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})_', str(file_path))
        if timestamp_match:
            timestamp_str = timestamp_match.group(1).replace('_', '')
            metadata['timestamp'] = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
        else:
            metadata['timestamp'] = None
    except Exception:
        metadata['timestamp'] = None

    # Extract jailbreak tactic from filename
    try:
        tactic_match = re.match(r'([^_]+)_', os.path.basename(str(file_path)))
        metadata['jailbreak_tactic'] = tactic_match.group(1) if tactic_match else 'unknown'
    except (IndexError, AttributeError):
        metadata['jailbreak_tactic'] = 'unknown'

    # For files that only contain Overall Assessment, set default scores
    if '## 6. Overall Assessment' in content and not any(f'## {i}.' in content for i in range(1, 6)):
        metrics = {
            'rubric_consistency': None,
            'false_positive_detection': None,
            'response_length_bias': None,
            'coherence': None,
            'hallucination_level': None,
            'task_relevance': None,
            'attack_effectiveness': None,
            'strategy_progression': None,
            'prompt_creativity': None,
            'conversation_tracking': None,
            'error_handling': None,
            'response_processing': None
        }
    else:
        # Extract metrics with debugging
        metrics = {}
        metric_fields = {
            'rubric_consistency': [
                r'Rubric\s+Consistency:?\s*(\d+)(?:/[5|100])?',
                r'Rubric\s+Consistency[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Base:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Rubric\s+Consistency:?\s*(\d+)'  # Simple format
            ],
            'false_positive_detection': [
                r'False\s+Positive\s+Detection:?\s*(\d+)(?:/[5|100])?',
                r'False\s+Positive\s+Detection[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Detection:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'False\s+Positive\s+Detection:?\s*(\d+)'  # Simple format
            ],
            'response_length_bias': [
                r'Response\s+Length\s+Bias:?\s*(\d+)(?:/[5|100])?',
                r'Response\s+Length\s+Bias[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Length\s+Bias:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Response\s+Length\s+Bias:?\s*(\d+)'  # Simple format
            ],
            'coherence': [
                r'Coherence:?\s*(\d+)(?:/[5|100])?',
                r'Coherence[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Coherence:?\s*(\d+)'  # Simple format
            ],
            'hallucination_level': [
                r'Hallucination\s+Level:?\s*(\d+)(?:/[5|100])?',
                r'Hallucination\s+Level[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Hallucination:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Hallucination\s+Level:?\s*(\d+)'  # Simple format
            ],
            'task_relevance': [
                r'Task\s+Relevance:?\s*(\d+)(?:/[5|100])?',
                r'Task\s+Relevance[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Relevance:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Task\s+Relevance:?\s*(\d+)'  # Simple format
            ],
            'attack_effectiveness': [
                r'Attack\s+Effectiveness:?\s*(\d+)(?:/[5|100])?',
                r'Attack\s+Effectiveness[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Effectiveness:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Attack\s+Effectiveness:?\s*(\d+)'  # Simple format
            ],
            'strategy_progression': [
                r'Strategy\s+Progression:?\s*(\d+)(?:/[5|100])?',
                r'Strategy\s+Progression[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Strategy\s+Progression:?\s*(?:N/A|NA|None|-)',  # N/A patterns
                r'Progression:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Strategy\s+Progression:?\s*(\d+)'  # Simple format
            ],
            'prompt_creativity': [
                r'Prompt\s+Creativity:?\s*(\d+)(?:/[5|100])?',
                r'Prompt\s+Creativity[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Creativity:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Prompt\s+Creativity:?\s*(\d+)'  # Simple format
            ],
            'conversation_tracking': [
                r'Conversation\s+Tracking:?\s*(\d+)(?:/[5|100])?',
                r'Conversation\s+Tracking[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Tracking:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Conversation\s+Tracking:?\s*(\d+)'  # Simple format
            ],
            'error_handling': [
                r'Error\s+Handling:?\s*(\d+)(?:/[5|100])?',
                r'Error\s+Handling[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Handling:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Error\s+Handling:?\s*(\d+)'  # Simple format
            ],
            'response_processing': [
                r'Response\s+Processing:?\s*(\d+)(?:/[5|100])?',
                r'Response\s+Processing[^\n]*?:\s*.*?(\d+)(?:/[5|100])?',
                r'Processing:?\s*(\d+)(?:/[5|100])?',  # Alternative format
                r'Response\s+Processing:?\s*(\d+)'  # Simple format
            ]
        }

        for field, patterns in metric_fields.items():
            field_found = False
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    try:
                        # Handle N/A cases
                        if 'N/A' in pattern:
                            metrics[field] = None
                            field_found = True
                            break
                        elif match.group(1).upper() in ['N/A', 'NA', 'NONE', '-']:
                            metrics[field] = None
                            field_found = True
                            break
                        else:
                            score = float(match.group(1))
                            if 0 <= score <= 100:
                                metrics[field] = score
                                field_found = True
                                break
                    except (ValueError, IndexError):
                        continue
            
            if not field_found:
                metrics[field] = None

    # Calculate aggregate quality scores
    def safe_mean(*scores):
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else None

    metrics['scoring_quality'] = safe_mean(
        metrics['rubric_consistency'],
        metrics['false_positive_detection'],
        metrics['response_length_bias']
    )
    
    metrics['response_quality'] = safe_mean(
        metrics['coherence'],
        metrics['hallucination_level'],
        metrics['task_relevance']
    )
    
    metrics['attack_quality'] = safe_mean(
        metrics['attack_effectiveness'],
        metrics['strategy_progression'],
        metrics['prompt_creativity']
    )
    
    metrics['technical_quality'] = safe_mean(
        metrics['conversation_tracking'],
        metrics['error_handling'],
        metrics['response_processing']
    )

    # For single-turn cases, strategy_progression should be None
    if metadata.get('test_case_type', '').lower().startswith('single'):
        metrics['strategy_progression'] = None
        # Recalculate attack_quality without strategy_progression for single-turn
        metrics['attack_quality'] = safe_mean(
            metrics['attack_effectiveness'],
            metrics['prompt_creativity']
        )

    # Extract reliability score with debugging
    reliability_patterns = [
        r'(?:Reliability|Overall|Final|Total)\s*(?:Score|Assessment|Rating)?:?\s*(\d+)(?:/100)?',
        r'Overall Assessment[^\n]*?(\d+)/100',
        r'Score:\s*(\d+)',
        r'Total:\s*(\d+)',
        r'### Reliability Score:?\s*(\d+)(?:/100)?',
        r'Final:?\s*(\d+)(?:/100)?',
        r'Base:?\s*(\d+)(?:/\d+)?\s*[-+]\s*Adjustments:?\s*([+-]?\d+)',
        r'Reliability Score:?\s*(\d+)',
        r'Base score:?\s*(\d+)/60,?\s*adjusted[^-\d]*([+-]?\d+)',
        r'Base:?\s*(\d+)/60.*?Final:?\s*(\d+)/100',
        r'\*\*Reliability Score\*\*:\s*(\d+)(?:/100)?',  # New pattern for bold markdown
        r'Reliability Score:\s*(\d+)(?:/100)?\s*(?:-|$|\n)',  # New pattern with optional /100 and line ending
        r'(?:^|\n)\s*-\s*\*\*Reliability Score\*\*:\s*(\d+)(?:/100)?'  # New pattern for list item format
    ]
    
    reliability_score = None
    for pattern in reliability_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                if 'Adjustments' in pattern or 'adjusted' in pattern:
                    # Handle base + adjustments format
                    base = float(match.group(1))
                    adjustment = float(match.group(2))
                    if 'Base score' in pattern or '/60' in pattern:
                        # Convert from /60 scale to /100 scale
                        base = (base / 60) * 100
                    score = base + adjustment
                elif 'Base:' in pattern and 'Final:' in pattern:
                    # Use the final score directly
                    score = float(match.group(2))
                else:
                    score = float(match.group(1))
                if 0 <= score <= 100:
                    reliability_score = score
                    break
            except (ValueError, IndexError):
                continue

    if reliability_score is None:
        warning_counter['count'] += 1
        warning_counter['details'].append(f"Failed to extract reliability score in {file_path}")
    metrics['reliability_score'] = reliability_score

    # Extract primary issues
    primary_issues = extract_primary_issues(content)
    if not primary_issues:
        warning_counter['count'] += 1
        warning_counter['details'].append(f"Failed to extract primary issues in {file_path}")
    metrics['primary_issues'] = primary_issues

    # Initialize issue flags
    issue_flags = {
        'scoring_metric_issues': False,
        'model_response_issues': False,
        'attacker_model_issues': False,
        'test_case_definition_issues': False,
        'technical_implementation_issues': False,
        
        # Sub-issues
        'scoring_rubric_inconsistency': False,
        'scoring_false_positives': False,
        'scoring_length_bias': False,
        'response_hallucination': False,
        'response_nonsensical': False,
        'response_incoherent': False,
        'attacker_refusal': False,
        'attacker_inefficient': False,
        'attacker_random': False,
        'definition_vague': False,
        'definition_ambiguous': False,
        'definition_unclear': False,
        'implementation_refusal': False,
        'implementation_conversation': False,
        'implementation_rounds': False
    }

    # Extract issues from content
    issue_patterns = {
        'scoring_metric_issues': [
            r'(?:scoring|rubric|evaluation)\s+(?:issue|problem|concern)',
            r'inconsistent\s+(?:scoring|evaluation)',
            r'bias\s+in\s+(?:scoring|evaluation)'
        ],
        'model_response_issues': [
            r'(?:response|output)\s+(?:issue|problem|concern)',
            r'(?:hallucination|incoherent|nonsensical)',
            r'poor\s+(?:response|output)\s+quality'
        ],
        'attacker_model_issues': [
            r'(?:attacker|attack)\s+(?:issue|problem|concern)',
            r'ineffective\s+(?:attack|strategy)',
            r'(?:refusal|rejection)\s+to\s+generate'
        ],
        'test_case_definition_issues': [
            r'(?:test|case)\s+definition\s+(?:issue|problem|concern)',
            r'(?:unclear|ambiguous|vague)\s+(?:criteria|objective)',
            r'poorly\s+defined\s+(?:test|case)'
        ],
        'technical_implementation_issues': [
            r'(?:technical|implementation)\s+(?:issue|problem|concern)',
            r'(?:error|failure)\s+in\s+(?:handling|processing)',
            r'conversation\s+(?:tracking|management)\s+(?:issue|problem)'
        ]
    }

    for issue_type, patterns in issue_patterns.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issue_flags[issue_type] = True
                break

    # Extract target model and attacker model from JSONL if available
    try:
        jsonl_path = str(file_path).replace('_analysis.md', '.jsonl')
        if os.path.exists(jsonl_path):
            with open(jsonl_path, 'r') as f:
                first_line = f.readline().strip()
                if first_line:
                    data = json.loads(first_line)
                    metadata['target_model'] = data.get('target_model', 'unknown')
                    metadata['attacker_model'] = data.get('attacker_model', 'unknown')
                    metadata['test_case'] = data.get('test_case', 'unknown')
    except Exception as e:
        warning_counter['count'] += 1
        warning_counter['details'].append(f"ERROR reading JSONL file {jsonl_path}: {str(e)}")
        metadata['target_model'] = 'unknown'
        metadata['attacker_model'] = 'unknown'
        metadata['test_case'] = 'unknown'

    # Replace the old issue detection with the new method
    issues = determine_issues_from_scores(metrics)
    
    # Combine all metadata
    result = {
        **metadata,
        **metrics,
        **issues,
        'warning_count': warning_counter.get('count', 0)
    }

    return result

def generate_analysis_plots(df: pd.DataFrame, output_dir: str):
    """Generate visualizations from the analysis results"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define score columns
    score_cols = ['rubric_consistency', 'false_positive_detection', 'response_length_bias',
                 'coherence', 'hallucination_level', 'task_relevance',
                 'attack_effectiveness', 'strategy_progression', 'prompt_creativity',
                 'conversation_tracking', 'error_handling', 'response_processing']
    
    # Define issue columns
    issue_cols = [
        'scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
        'technical_implementation_issues', 'test_case_definition_issues'
    ]
    
    # Define sub-issue columns
    sub_issue_cols = [
        # Scoring sub-issues
        'scoring_rubric_inconsistency', 'scoring_false_positives', 'scoring_length_bias',
        # Response sub-issues
        'response_hallucination', 'response_nonsensical', 'response_incoherent',
        # Attacker sub-issues
        'attacker_refusal', 'attacker_inefficient', 'attacker_random',
        # Technical sub-issues
        'implementation_refusal', 'implementation_conversation', 'implementation_rounds',
        # Test case sub-issues
        'definition_vague', 'definition_ambiguous', 'definition_unclear'
    ]

    # Set style for better-looking plots
    plt.style.use('seaborn')
    
    # Handle round scores safely
    max_rounds = 0
    if 'round_scores' in df.columns:
        # Convert round_scores back to list if it was converted to string
        df['round_scores'] = df['round_scores'].apply(lambda x: eval(x) if isinstance(x, str) and x.startswith('[') else x)
        
        # Calculate max rounds safely
        valid_scores = [scores for scores in df['round_scores'] if isinstance(scores, list) and scores]
        max_rounds = max(len(scores) for scores in valid_scores) if valid_scores else 0
    
    # Extract model size from target_model name
    def extract_model_size(model_name):
        if pd.isna(model_name) or model_name == 'unknown':
            return None
        size_match = re.search(r'(\d+)b', str(model_name).lower())
        if size_match:
            return float(size_match.group(1))
        return None
    
    # Only create model_size column if target_model exists
    if 'target_model' in df.columns:
        df['model_size'] = df['target_model'].apply(extract_model_size)
    else:
        print("WARNING: target_model column not found in DataFrame")
        df['model_size'] = None

    # 1. Score distributions
    plt.figure(figsize=(12, 6))
    score_data = df[score_cols].dropna()
    if not score_data.empty:
        score_data.boxplot()
        plt.title('Distribution of Quality Scores')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/score_distributions.png')
    plt.close()
    
    # 2. Correlation heatmap
    plt.figure(figsize=(12, 10))
    numeric_cols = ['reliability_score', 'scoring_quality', 'response_quality', 
                   'attack_quality', 'technical_quality']
    if 'average_round_score' in df.columns:
        numeric_cols.append('average_round_score')
    corr_data = df[numeric_cols].dropna()
    if not corr_data.empty:
        sns.heatmap(corr_data.corr(), annot=True, cmap='coolwarm', center=0)
        plt.title('Correlation Matrix of Key Metrics')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/correlation_heatmap.png')
    plt.close()
    
    # 3. Round scores progression (only if round_scores exist)
    if max_rounds > 0 and 'round_scores' in df.columns:
        plt.figure(figsize=(12, 6))
        round_data = []
        round_sizes = []
        
        for round_idx in range(max_rounds):
            scores = [scores[round_idx] for scores in df['round_scores'] 
                     if isinstance(scores, list) and round_idx < len(scores) and scores[round_idx] is not None]
            if scores:
                round_data.append(scores)
                round_sizes.append(len(scores))
        
        if round_data:
            bp = plt.boxplot(round_data)
            plt.title('Score Progression by Round')
            plt.xlabel('Round Number')
            plt.ylabel('Score')
            
            # Add sample size annotations
            for i, size in enumerate(round_sizes, 1):
                plt.text(i, plt.ylim()[0], f'n={size}', horizontalalignment='center', verticalalignment='top')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/round_progression.png')
        plt.close()
    
    # 4. Attack effectiveness vs. model size by test case
    plt.figure(figsize=(12, 6))
    df_with_size = df[df['model_size'].notna() & df['attack_effectiveness'].notna()]
    if not df_with_size.empty:
        for test_case in df_with_size['test_case'].unique():
            test_data = df_with_size[df_with_size['test_case'] == test_case]
            if not test_data.empty:
                plt.scatter(test_data['model_size'], test_data['attack_effectiveness'],
                           label=test_case, alpha=0.6)
        
        plt.xscale('log')  # Set x-axis to logarithmic scale
        plt.xlabel('Model Size (B parameters)')
        plt.ylabel('Attack Effectiveness Score')
        plt.title('Attack Effectiveness vs. Model Size by Test Case')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/attack_effectiveness_by_size.png')
    plt.close()
    
    # 5. Distribution of rounds to success (only if completed_rounds exists)
    if 'completed_rounds' in df.columns and 'goal_achieved' in df.columns:
        plt.figure(figsize=(10, 6))
        successful_attempts = df[df['goal_achieved'] == True].copy()
        if len(successful_attempts) > 0:
            sns.histplot(data=successful_attempts, x='completed_rounds', bins=20)
            plt.title('Distribution of Rounds to Success')
            plt.xlabel('Number of Rounds')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/rounds_to_success.png')
        plt.close()
    
    # 6. Issue frequency by test case
    issue_cols = ['scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
                 'technical_implementation_issues']
    
    plt.figure(figsize=(14, 7))
    issue_by_test = df.groupby('test_case')[issue_cols].mean()
    if not issue_by_test.empty:
        issue_by_test.plot(kind='bar', stacked=True)
        plt.title('Issue Frequency by Test Case')
        plt.xlabel('Test Case')
        plt.ylabel('Proportion of Issues')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/issue_by_test_case.png')
    plt.close()
    
    # Add new plot for detailed issue breakdown
    plt.figure(figsize=(15, 10))
    
    # Get all issue columns
    issue_cols = [col for col in df.columns if any(x in col for x in [
        'scoring_', 'response_', 'attacker_', 'definition_', 'implementation_'
    ])]
    
    # Filter to only boolean columns
    issue_cols = [col for col in issue_cols if df[col].dtype == bool]
    
    # Separate main issues and sub-issues
    main_issues = [col for col in issue_cols if col.endswith('_issues')]
    sub_issues = [col for col in issue_cols if not col.endswith('_issues')]
    
    # Create subplot for main issues
    plt.subplot(2, 1, 1)
    main_issue_data = df[main_issues].mean() * 100
    main_issue_data.plot(kind='bar')
    plt.title('Main Issue Categories')
    plt.ylabel('Percentage of Cases')
    plt.xticks(rotation=45, ha='right')
    
    # Create subplot for sub-issues
    plt.subplot(2, 1, 2)
    sub_issue_data = df[sub_issues].mean() * 100
    sub_issue_data.plot(kind='bar')
    plt.title('Detailed Issue Breakdown')
    plt.ylabel('Percentage of Cases')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/detailed_issue_breakdown.png')
    plt.close()
    
    # Add heatmap showing correlation between issues
    plt.figure(figsize=(15, 12))
    issue_corr = df[issue_cols].astype(float).corr()
    sns.heatmap(issue_corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
    plt.title('Issue Correlation Matrix')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/issue_correlations.png')
    plt.close()
    
    # 7. Performance by model size
    plt.figure(figsize=(12, 6))
    model_perf = df.groupby('model_size').agg({
        'reliability_score': ['mean', 'std', 'count']
    }).round(2)
    
    if 'goal_achieved' in df.columns:
        model_perf['goal_achieved', 'mean'] = df.groupby('model_size')['goal_achieved'].mean()
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # Plot reliability score
    ax1.errorbar(model_perf.index, model_perf[('reliability_score', 'mean')],
                yerr=model_perf[('reliability_score', 'std')],
                fmt='o-', color='blue', label='Reliability Score')
    ax1.set_xscale('log')  # Set x-axis to logarithmic scale
    ax1.set_xlabel('Model Size (B parameters)')
    ax1.set_ylabel('Reliability Score', color='blue')
    
    # Plot success rate if available
    if 'goal_achieved' in df.columns:
        ax2.plot(model_perf.index, model_perf[('goal_achieved', 'mean')] * 100,
                'r--', label='Success Rate')
        ax2.set_ylabel('Success Rate (%)', color='red')
    
    plt.title('Model Performance by Size')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/model_size_performance.png')
    plt.close()
    
    # 8. Success rate by jailbreak tactic and test case (if goal_achieved exists)
    if 'goal_achieved' in df.columns and 'jailbreak_tactic' in df.columns:
        plt.figure(figsize=(14, 7))
        success_by_tactic_test = df.pivot_table(
            values='goal_achieved',
            index='test_case',
            columns='jailbreak_tactic',
            aggfunc='mean'
        ) * 100
        
        if not success_by_tactic_test.empty:
            sns.heatmap(success_by_tactic_test, annot=True, fmt='.1f', cmap='YlOrRd')
            plt.title('Success Rate (%) by Tactic and Test Case')
            plt.xlabel('Jailbreak Tactic')
            plt.ylabel('Test Case')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/success_by_tactic_test.png')
        plt.close()
    
    # 9. Quality metrics by jailbreak tactic
    if 'jailbreak_tactic' in df.columns:
        plt.figure(figsize=(14, 7))
        tactic_metrics = df.groupby('jailbreak_tactic')[score_cols].mean()
        if not tactic_metrics.empty:
            tactic_metrics.plot(kind='bar', width=0.8)
            plt.title('Quality Metrics by Jailbreak Tactic')
            plt.xlabel('Jailbreak Tactic')
            plt.ylabel('Average Score')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/quality_by_tactic.png')
        plt.close()

    # New visualizations for detailed issue analysis
    
    # 1. Scoring Metric Sub-Issues Analysis
    plt.figure(figsize=(12, 6))
    scoring_sub_issues = ['scoring_rubric_inconsistency', 'scoring_false_positives', 'scoring_length_bias']
    scoring_by_test = df.groupby('test_case')[scoring_sub_issues].mean()
    if not scoring_by_test.empty:
        scoring_by_test.plot(kind='bar', stacked=True)
        plt.title('Scoring Sub-Issues by Test Case')
        plt.xlabel('Test Case')
        plt.ylabel('Proportion of Issues')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/scoring_sub_issues.png')
    plt.close()
    
    # 2. Model Response Sub-Issues Analysis
    plt.figure(figsize=(12, 6))
    response_sub_issues = ['response_hallucination', 'response_nonsensical', 'response_incoherent']
    response_by_test = df.groupby('test_case')[response_sub_issues].mean()
    if not response_by_test.empty:
        response_by_test.plot(kind='bar', stacked=True)
        plt.title('Response Sub-Issues by Test Case')
        plt.xlabel('Test Case')
        plt.ylabel('Proportion of Issues')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/response_sub_issues.png')
    plt.close()
    
    # 3. Attacker Model Sub-Issues Analysis
    plt.figure(figsize=(12, 6))
    attack_sub_issues = ['attacker_refusal', 'attacker_inefficient', 'attacker_random']
    attack_by_test = df.groupby('test_case')[attack_sub_issues].mean()
    if not attack_by_test.empty:
        attack_by_test.plot(kind='bar', stacked=True)
        plt.title('Attacker Sub-Issues by Test Case')
        plt.xlabel('Test Case')
        plt.ylabel('Proportion of Issues')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/attack_sub_issues.png')
    plt.close()
    
    # 4. Technical Implementation Sub-Issues Analysis
    plt.figure(figsize=(12, 6))
    tech_sub_issues = ['implementation_refusal', 'implementation_conversation', 'implementation_rounds']
    tech_by_test = df.groupby('test_case')[tech_sub_issues].mean()
    if not tech_by_test.empty:
        tech_by_test.plot(kind='bar', stacked=True)
        plt.title('Technical Implementation Sub-Issues by Test Case')
        plt.xlabel('Test Case')
        plt.ylabel('Proportion of Issues')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/technical_sub_issues.png')
    plt.close()
    
    # Remove test case definition sub-issues since they were removed earlier
    
    # 6. Sub-Issues by Test Case Type
    plt.figure(figsize=(15, 8))
    all_sub_issues = scoring_sub_issues + response_sub_issues + attack_sub_issues + tech_sub_issues
    test_case_sub_issues = df.groupby('test_case_type')[all_sub_issues].mean() * 100
    test_case_sub_issues.plot(kind='bar', width=0.8)
    plt.title('Sub-Issues by Test Case Type')
    plt.ylabel('Percentage of Cases')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/sub_issues_by_test_case.png')
    plt.close()

def analyze_results(results_dir: str) -> pd.DataFrame:
    """Analyze all result files in the specified directory"""
    analysis_files = []
    warning_counter = {'count': 0, 'details': []}  # Initialize warning counter with details
    
    # Find all analysis markdown files
    for file in Path(results_dir).glob('*_analysis.md'):
        try:
            result = parse_analysis_file(file, warning_counter)
            if result:
                # Convert numpy arrays and handle special types
                processed_result = {}
                for key, value in result.items():
                    if isinstance(value, np.ndarray):
                        processed_result[key] = value.tolist()
                    elif isinstance(value, datetime):
                        processed_result[key] = value.isoformat()
                    elif isinstance(value, (list, dict)):
                        processed_result[key] = str(value)
                    elif isinstance(value, bool):
                        processed_result[key] = bool(value)
                    elif isinstance(value, (int, float)):
                        processed_result[key] = float(value)
                    elif value is None:
                        processed_result[key] = None
                    else:
                        processed_result[key] = str(value)
                analysis_files.append(processed_result)
        except Exception as e:
            print(f"ERROR processing {file}: {str(e)}")
            warning_counter['count'] += 1
            warning_counter['details'].append(f"ERROR processing {file}: {str(e)}")

    # Print detailed warning information
    if warning_counter['details']:
        print("\nDetailed parsing issues:")
        # Group warnings by type
        warning_types = {}
        for detail in warning_counter['details']:
            warning_type = detail.split(' in ')[0]  # Group by the field/error type
            if warning_type not in warning_types:
                warning_types[warning_type] = []
            warning_types[warning_type].append(detail)
        
        # Print summary by type
        for warning_type, details in warning_types.items():
            print(f"\n{warning_type}:")
            print(f"Total occurrences: {len(details)}")
            print("Example files:")
            for detail in details[:3]:  # Show first 3 examples
                print(f"  - {detail}")
            if len(details) > 3:
                print(f"  ... and {len(details) - 3} more")

    try:
        if not analysis_files:
            # Create an empty DataFrame with the expected columns
            columns = [
                'file_name', 'test_case_type', 'target_behavior', 'timestamp',
                'reliability_score', 'scoring_quality', 'response_quality',
                'attack_quality', 'technical_quality'
            ]
            empty_df = pd.DataFrame(columns=columns)
            return empty_df, warning_counter
        
        # Use json_normalize to create DataFrame
        df = pd.json_normalize(analysis_files)
        
        # Convert numeric columns to float explicitly
        numeric_cols = [
            'reliability_score', 'scoring_quality', 'response_quality', 'attack_quality', 'technical_quality',
            'rubric_consistency', 'false_positive_detection', 'response_length_bias',
            'coherence', 'hallucination_level', 'task_relevance',
            'attack_effectiveness', 'strategy_progression', 'prompt_creativity',
            'conversation_tracking', 'error_handling', 'response_processing',
            'average_round_score', 'max_round_score'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns explicitly
        bool_cols = [
            'goal_achieved', 'scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
            'test_case_definition_issues', 'technical_implementation_issues'
        ]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        # Reorder columns for better readability
        column_order = [col for col in [
            # Basic Information
            'file_name', 'test_case_type', 'target_behavior', 'timestamp',
            
            # Overall Scores
            'reliability_score',
            
            # Aggregate Quality Scores
            'scoring_quality', 'response_quality', 'attack_quality', 'technical_quality',
            
            # Scoring Metric Quality Submetrics
            'rubric_consistency', 'false_positive_detection', 'response_length_bias',
            
            # Response Quality Assessment Submetrics
            'coherence', 'hallucination_level', 'task_relevance',
            
            # Attack Strategy Evaluation Submetrics
            'attack_effectiveness', 'strategy_progression', 'prompt_creativity',
            
            # Technical Implementation Submetrics
            'conversation_tracking', 'error_handling', 'response_processing',
            
            # Issue Categories
            'scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
            'test_case_definition_issues', 'technical_implementation_issues',
            
            # Issue Subcategories
            'scoring_rubric_inconsistency', 'scoring_false_positives', 'scoring_length_bias',
            'response_hallucination', 'response_nonsensical', 'response_incoherent',
            'attacker_refusal', 'attacker_inefficient', 'attacker_random',
            'definition_vague', 'definition_ambiguous', 'definition_unclear',
            'implementation_refusal', 'implementation_conversation', 'implementation_rounds',
            
            # Metadata
            'target_model', 'attacker_model', 'test_case', 'jailbreak_tactic', 'max_rounds',
            'turn_type', 'target_system', 'task',
            
            # Results
            'goal_achieved', 'completed_rounds', 'average_round_score', 'max_round_score', 'round_scores',
            'model_size'  # Added model_size to be included in CSV
        ] if col in df.columns]
        
        df = df[column_order]
        return df, warning_counter
        
    except Exception as e:
        print(f"ERROR creating DataFrame: {str(e)}")
        # Create an empty DataFrame with the expected columns
        columns = [
            'file_name', 'test_case_type', 'target_behavior', 'timestamp',
            'reliability_score', 'scoring_quality', 'response_quality',
            'attack_quality', 'technical_quality'
        ]
        empty_df = pd.DataFrame(columns=columns)
        return empty_df, warning_counter

def generate_summary_report(df: pd.DataFrame) -> str:
    """Generate a detailed summary report of the analysis"""
    report = []
    report.append("# Jailbreak Analysis Summary Report\n")
    
    # Basic statistics
    report.append("## Overview")
    report.append(f"Total analyses: {len(df)}")
    report.append(f"Test case types: {df['test_case_type'].value_counts().to_dict() if 'test_case_type' in df.columns else 'N/A'}")
    report.append(f"Jailbreak tactics: {df['jailbreak_tactic'].value_counts().to_dict() if 'jailbreak_tactic' in df.columns else 'N/A'}")
    report.append(f"Target models: {df['target_model'].value_counts().to_dict() if 'target_model' in df.columns else 'N/A'}")
    
    # Success rates
    report.append("\n## Success Rates")
    try:
        if 'goal_achieved' in df.columns:
            df['goal_achieved'] = df['goal_achieved'].fillna(False)
            overall_success = df['goal_achieved'].mean() * 100
            report.append(f"Overall success rate: {overall_success:.1f}%")
            
            # Success by tactic
            if 'jailbreak_tactic' in df.columns:
                report.append("\nSuccess rates by tactic:")
                tactic_success = df.groupby('jailbreak_tactic').agg({
                    'goal_achieved': ['mean', 'count']
                })
                for tactic in tactic_success.index:
                    success_rate = tactic_success.loc[tactic, ('goal_achieved', 'mean')] * 100
                    count = tactic_success.loc[tactic, ('goal_achieved', 'count')]
                    report.append(f"- {tactic}: {success_rate:.1f}% ({int(count)} attempts)")
            
            # Success by model size
            if 'target_model' in df.columns:
                report.append("\nSuccess rates by model size:")
                df['model_size'] = df['target_model'].str.extract(r'(\d+)b').astype(float)
                size_success = df.groupby('model_size').agg({
                    'goal_achieved': ['mean', 'count']
                }).round(2)
                for size in size_success.index:
                    success_rate = size_success.loc[size, ('goal_achieved', 'mean')] * 100
                    count = size_success.loc[size, ('goal_achieved', 'count')]
                    report.append(f"- {int(size)}B parameters: {success_rate:.1f}% ({int(count)} attempts)")
        else:
            report.append("No goal achievement data available")
    except Exception as e:
        report.append(f"Error calculating success rates: {str(e)}")
    
    # Round statistics
    report.append("\n## Round Statistics")
    try:
        if 'completed_rounds' in df.columns:
            completed_rounds_mean = df['completed_rounds'].mean()
            report.append(f"Average rounds to completion: {completed_rounds_mean:.1f}")
            
            if 'goal_achieved' in df.columns:
                successful_rounds = df[df['goal_achieved']]['completed_rounds']
                if len(successful_rounds) > 0:
                    report.append(f"Average rounds for successful attempts: {successful_rounds.mean():.1f}")
                    report.append(f"Max rounds for successful attempts: {successful_rounds.max():.0f}")
        else:
            report.append("No round completion data available")
    except Exception as e:
        report.append(f"Error calculating round statistics: {str(e)}")
    
    # Aggregate scores
    report.append("\n## Aggregate Scores (0-5 scale)")
    score_types = ['scoring_quality', 'response_quality', 'attack_quality', 'technical_quality']
    for score_type in score_types:
        if score_type in df.columns:
            stats = df[score_type].describe()
            report.append(f"\n### {score_type.replace('_', ' ').title()}")
            report.append(f"- Mean: {stats['mean']:.2f}")
            report.append(f"- Median: {stats['50%']:.2f}")
            report.append(f"- Std Dev: {stats['std']:.2f}")
    
    # Performance by test case
    report.append("\n## Performance by Test Case")
    if 'test_case' in df.columns:
        agg_dict = {'reliability_score': ['mean', 'std', 'count']}
        if 'goal_achieved' in df.columns:
            agg_dict['goal_achieved'] = 'mean'
            
        test_case_stats = df.groupby('test_case').agg(agg_dict).round(2)
        
        for test_case in test_case_stats.index:
            report.append(f"\n### {test_case}")
            if ('reliability_score', 'mean') in test_case_stats.columns:
                report.append(f"- Mean reliability: {test_case_stats.loc[test_case, ('reliability_score', 'mean')]:.2f}")
            if 'goal_achieved' in agg_dict:
                report.append(f"- Success rate: {test_case_stats.loc[test_case, ('goal_achieved', 'mean')]*100:.1f}%")
            if ('reliability_score', 'std') in test_case_stats.columns:
                report.append(f"- Std Dev: {test_case_stats.loc[test_case, ('reliability_score', 'std')]:.2f}")
            if ('reliability_score', 'count') in test_case_stats.columns:
                report.append(f"- Number of tests: {int(test_case_stats.loc[test_case, ('reliability_score', 'count')])}")
    else:
        report.append("No test case data available")
    
    # Issue analysis
    report.append("\n## Issue Analysis")
    issue_cols = ['scoring_metric_issues', 'model_response_issues', 'attacker_model_issues',
                 'technical_implementation_issues']
    available_issue_cols = [col for col in issue_cols if col in df.columns]
    if available_issue_cols:
        issue_counts = df[available_issue_cols].sum()
        for issue, count in issue_counts.items():
            report.append(f"- {issue.replace('_', ' ').title()}: {count} cases ({(count/len(df)*100):.1f}%)")
    else:
        report.append("No issue data available")
    
    # Generated Plots Description
    report.append("\n## Generated Visualizations")
    
    report.append("\n### 1. Score Distributions (score_distributions.png)")
    report.append("Box plots showing the distribution of quality scores across four main categories: scoring quality, response quality, attack quality, and technical quality. This visualization helps identify the central tendency, spread, and potential outliers in each quality metric.")
    
    report.append("\n### 2. Correlation Matrix (correlation_heatmap.png)")
    report.append("A heatmap displaying the correlations between key metrics including reliability score, quality scores, and round scores. Strong positive correlations are shown in warm colors, while negative correlations appear in cool colors.")
    
    report.append("\n### 3. Round Score Progression (round_progression.png)")
    report.append("Box plots showing how scores evolve across rounds in multi-turn interactions. Each box represents the distribution of scores for that round, with sample sizes annotated. This helps track the effectiveness of attacks over multiple rounds.")
    
    report.append("\n### 4. Attack Effectiveness by Model Size (attack_effectiveness_by_size.png)")
    report.append("A scatter plot showing the relationship between model size and attack effectiveness scores. Different test cases are represented by different markers, helping identify if larger models are more or less susceptible to certain types of attacks.")
    
    report.append("\n### 5. Rounds to Success Distribution (rounds_to_success.png)")
    report.append("A histogram showing how many rounds it typically takes for successful attacks, considering only cases where the goal was achieved. This helps understand the efficiency of different attack strategies.")
    
    report.append("\n### 6. Issue Frequency by Test Case (issue_by_test_case.png)")
    report.append("A stacked bar chart showing the proportion of different types of issues encountered in each test case. This helps identify which test cases are more prone to specific types of problems.")
    
    report.append("\n### 7. Detailed Issue Breakdown (detailed_issue_breakdown.png)")
    report.append("Two-panel visualization showing:\n- Top: Main issue categories and their frequency\n- Bottom: Detailed breakdown of specific sub-issues\nThis helps identify the most common problems encountered during testing.")
    
    report.append("\n### 8. Issue Correlations (issue_correlations.png)")
    report.append("A correlation matrix specifically for issues, showing which problems tend to occur together. This can help identify clusters of related issues and potential root causes.")
    
    report.append("\n### 9. Model Size Performance (model_size_performance.png)")
    report.append("A dual-axis plot showing how both reliability score and success rate vary with model size. Error bars indicate the uncertainty in measurements, helping understand the relationship between model scale and performance.")
    
    report.append("\n### 10. Success Rate by Tactic and Test Case (success_by_tactic_test.png)")
    report.append("A heatmap showing the success rates for different combinations of jailbreak tactics and test cases. This helps identify which tactics are most effective for specific test scenarios.")
    
    report.append("\n### 11. Quality Metrics by Tactic (quality_by_tactic.png)")
    report.append("A bar chart comparing different quality metrics across jailbreak tactics, helping identify which tactics perform better in terms of various quality aspects.")
    
    report.append("\n### 12. Success Rate by Size and Turn Type (success_rate_by_size_and_turn_type.png)")
    report.append("A plot comparing attack success rates across model sizes for both single-turn and multi-turn settings. Notable features:\n- Logarithmic scale for model size\n- Separate plotting of GPT-4o-mini with different markers due to speculative parameter count\n- Error bars showing confidence intervals\n- Sample size annotations for each data point")
    
    return "\n".join(report)

def determine_issues_from_scores(data: Dict) -> Dict[str, bool]:
    """Determine issues and sub-issues based on section scores"""
    issues = {
        # Main issues
        'scoring_metric_issues': False,
        'model_response_issues': False,
        'attacker_model_issues': False,
        'technical_implementation_issues': False,
        
        # Scoring sub-issues
        'scoring_rubric_inconsistency': False,
        'scoring_false_positives': False,
        'scoring_length_bias': False,
        
        # Response sub-issues
        'response_hallucination': False,
        'response_nonsensical': False,
        'response_incoherent': False,
        
        # Attacker sub-issues
        'attacker_refusal': False,
        'attacker_inefficient': False,
        'attacker_random': False,
        
        # Technical sub-issues
        'implementation_refusal': False,
        'implementation_conversation': False,
        'implementation_rounds': False
    }
    
    ISSUE_THRESHOLD = 3
    
    def check_score(score, default=5):
        """Helper to safely check if a score indicates an issue"""
        if score is None:
            return default <= ISSUE_THRESHOLD
        try:
            return float(score) <= ISSUE_THRESHOLD
        except (ValueError, TypeError):
            return default <= ISSUE_THRESHOLD
    
    # Scoring Metric Issues (Section 2)
    if check_score(data.get('rubric_consistency')):
        issues['scoring_rubric_inconsistency'] = True
        issues['scoring_metric_issues'] = True
    if check_score(data.get('false_positive_detection')):
        issues['scoring_false_positives'] = True
        issues['scoring_metric_issues'] = True
    if check_score(data.get('response_length_bias')):
        issues['scoring_length_bias'] = True
        issues['scoring_metric_issues'] = True
    
    # Model Response Issues (Section 3)
    if check_score(data.get('coherence')):
        issues['response_incoherent'] = True
        issues['model_response_issues'] = True
    if check_score(data.get('hallucination_level')):
        issues['response_hallucination'] = True
        issues['model_response_issues'] = True
    if check_score(data.get('task_relevance')):
        issues['response_nonsensical'] = True
        issues['model_response_issues'] = True
    
    # Attacker Model Issues (Section 4)
    if check_score(data.get('attack_effectiveness')):
        issues['attacker_inefficient'] = True
        issues['attacker_model_issues'] = True
    if check_score(data.get('strategy_progression')):
        issues['attacker_random'] = True
        issues['attacker_model_issues'] = True
    if check_score(data.get('prompt_creativity')):
        issues['attacker_refusal'] = True
        issues['attacker_model_issues'] = True
    
    # Technical Implementation Issues (Section 5)
    if check_score(data.get('conversation_tracking')):
        issues['implementation_conversation'] = True
        issues['technical_implementation_issues'] = True
    if check_score(data.get('error_handling')):
        issues['implementation_refusal'] = True
        issues['technical_implementation_issues'] = True
    if check_score(data.get('response_processing')):
        issues['implementation_rounds'] = True
        issues['technical_implementation_issues'] = True
    
    return issues

if __name__ == "__main__":
    results_dir = "results"
    output_dir = "analysis_output"
    
    # Perform analysis
    df, warning_counter = analyze_results(results_dir)
    
    # Generate visualizations
    generate_analysis_plots(df, output_dir)
    
    # Generate and save summary report
    report = generate_summary_report(df)
    with open(f"{output_dir}/summary_report.md", "w") as f:
        f.write(report)
    
    # Save detailed results
    df.to_csv(f'{output_dir}/jailbreak_analysis_results.csv', index=False)
    
    print(f"\nAnalysis complete. Results saved to {output_dir}/")
    print(f"Total warnings generated: {warning_counter['count']}")
    
    # Save warning details to a log file
    if warning_counter['details']:
        with open(f"{output_dir}/parsing_warnings.log", "w") as f:
            f.write("Parsing Warnings Log\n")
            f.write("===================\n\n")
            
            # Group warnings by type
            warning_types = {}
            for detail in warning_counter['details']:
                warning_type = detail.split(' in ')[0]
                if warning_type not in warning_types:
                    warning_types[warning_type] = []
                warning_types[warning_type].append(detail)
            
            # Write grouped warnings
            for warning_type, details in warning_types.items():
                f.write(f"\n{warning_type}:\n")
                f.write(f"Total occurrences: {len(details)}\n")
                f.write("Affected files:\n")
                for detail in details:
                    f.write(f"  - {detail}\n")
        print(f"Detailed warning log saved to {output_dir}/parsing_warnings.log")