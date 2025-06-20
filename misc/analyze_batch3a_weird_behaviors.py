#!/usr/bin/env python3
"""
Analysis script to detect weird behaviors in batch3A JSONL files.

Detects:
1. Having minus score
2. Having multiple goal_achieved field
3. Marked as goal_achieved True but no score 1.0
4. Marked as goal_achieved False but there is score 1.0
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

def analyze_jsonl_file(file_path):
    """Analyze a single JSONL file for weird behaviors."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        goal_achieved_count = 0
        goal_achieved_value = None
        scores = []
        negative_scores = []
        score_1_found = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                # Check for goal_achieved field
                if 'goal_achieved' in data:
                    goal_achieved_count += 1
                    goal_achieved_value = data['goal_achieved']
                
                # Check for scores
                if 'score' in data:
                    score = data['score']
                    scores.append((line_num, score))
                    
                    # Check for negative scores
                    if isinstance(score, (int, float)) and score < 0:
                        negative_scores.append((line_num, score))
                    
                    # Check for score = 1.0
                    if score == 1.0:
                        score_1_found = True
                        
            except json.JSONDecodeError as e:
                issues.append(f"JSON decode error on line {line_num}: {e}")
                
        # Issue 1: Negative scores
        if negative_scores:
            issues.append(f"NEGATIVE SCORES found: {negative_scores}")
        
        # Issue 2: Multiple goal_achieved fields
        if goal_achieved_count > 1:
            issues.append(f"MULTIPLE goal_achieved fields: found {goal_achieved_count} times")
        
        # Issue 3: goal_achieved True but no score 1.0
        if goal_achieved_value is True and not score_1_found:
            issues.append(f"goal_achieved=True but NO score=1.0 found. Scores: {[s[1] for s in scores]}")
        
        # Issue 4: goal_achieved False but there is score 1.0
        if goal_achieved_value is False and score_1_found:
            issues.append(f"goal_achieved=False but SCORE=1.0 found. All scores: {[s[1] for s in scores]}")
        
        return issues, {
            'goal_achieved_count': goal_achieved_count,
            'goal_achieved_value': goal_achieved_value,
            'scores': scores,
            'negative_scores': negative_scores,
            'score_1_found': score_1_found,
            'total_lines': len(lines)
        }
        
    except Exception as e:
        return [f"Error reading file: {e}"], None

def analyze_directory(directory_path):
    """Analyze all JSONL files in a directory."""
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        print(f"Error: Directory {directory_path} does not exist")
        return
    
    print(f"Analyzing directory: {directory_path}")
    print("=" * 80)
    
    total_files = 0
    files_with_issues = 0
    issue_summary = defaultdict(int)
    
    # Find all .jsonl files recursively
    jsonl_files = list(directory_path.rglob("*.jsonl"))
    
    if not jsonl_files:
        print("No .jsonl files found in directory")
        return
    
    for file_path in sorted(jsonl_files):
        total_files += 1
        relative_path = file_path.relative_to(directory_path)
        
        issues, stats = analyze_jsonl_file(file_path)
        
        if issues:
            files_with_issues += 1
            print(f"\n🚨 ISSUES FOUND in {relative_path}:")
            for issue in issues:
                print(f"   - {issue}")
                # Categorize issues
                if "NEGATIVE SCORES" in issue:
                    issue_summary["negative_scores"] += 1
                if "MULTIPLE goal_achieved" in issue:
                    issue_summary["multiple_goal_achieved"] += 1
                if "goal_achieved=True but NO score=1.0" in issue:
                    issue_summary["goal_true_no_score_1"] += 1
                if "goal_achieved=False but SCORE=1.0" in issue:
                    issue_summary["goal_false_has_score_1"] += 1
            
            if stats:
                print(f"   📊 Stats: goal_achieved={stats['goal_achieved_value']}, "
                      f"scores_count={len(stats['scores'])}, "
                      f"negative_scores={len(stats['negative_scores'])}, "
                      f"has_score_1={stats['score_1_found']}")
        else:
            print(f"✅ {relative_path}")
    
    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total files analyzed: {total_files}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Files without issues: {total_files - files_with_issues}")
    
    if issue_summary:
        print("\nISSUE BREAKDOWN:")
        print(f"  1. Files with negative scores: {issue_summary['negative_scores']}")
        print(f"  2. Files with multiple goal_achieved fields: {issue_summary['multiple_goal_achieved']}")
        print(f"  3. Files with goal_achieved=True but no score=1.0: {issue_summary['goal_true_no_score_1']}")
        print(f"  4. Files with goal_achieved=False but has score=1.0: {issue_summary['goal_false_has_score_1']}")
    else:
        print("\n🎉 No weird behaviors detected!")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_batch3a_weird_behaviors.py <directory_path>")
        print("Example: python analyze_batch3a_weird_behaviors.py /path/to/batch3A")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    analyze_directory(directory_path)

if __name__ == "__main__":
    main()