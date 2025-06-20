#!/usr/bin/env python3
"""
Backfill FP annotations from false_positive_annotations.jsonl

This script goes through all batch3A files, identifies successful attacks without
FP annotations, and backfills them from the centralized annotations file.
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List
import argparse

def load_all_annotations(annotations_file: str) -> Dict[str, Dict]:
    """Load all annotations indexed by filename."""
    annotations = {}
    with open(annotations_file, 'r') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                filename = ann['filename']
                annotations[filename] = ann
    return annotations

def check_file_has_fp_annotation(file_path: str) -> bool:
    """Check if a file already has FP annotations embedded."""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if 'fp_decision' in data:
                        return True
    except Exception:
        pass
    return False

def is_successful_attack(file_path: str) -> bool:
    """Check if this file represents a successful jailbreak attack."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Parse the config (first line)
        config = json.loads(lines[0])
        
        # Check if goal_achieved is True in config
        if config.get('goal_achieved') is True:
            return True
            
        # Also check for successful scores in conversation data
        for line in lines[1:]:
            if line.strip():
                try:
                    data = json.loads(line)
                    # Look for score = 1.0 or score = 1
                    if data.get('score') == 1.0 or data.get('score') == 1:
                        return True
                except:
                    continue
                    
        return False
    except Exception as e:
        print(f"Error checking success for {file_path}: {e}")
        return False

def embed_fp_annotation(file_path: str, annotation: Dict, dry_run: bool = False) -> bool:
    """Embed FP annotation into the experiment file."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        updated_lines = []
        annotation_added = False
        
        for line in lines:
            line = line.strip()
            if not line:
                updated_lines.append('')
                continue
                
            try:
                data = json.loads(line)
                
                # Add FP annotation to successful rounds
                should_annotate = False
                
                # Check for score-based success
                if 'score' in data:
                    if data['score'] == 1.0 or data['score'] == 1:
                        should_annotate = True
                
                # Check for goal_achieved at line level
                if data.get('goal_achieved') is True:
                    should_annotate = True
                
                # For conversation turns without explicit scores, be more liberal
                # This handles cases where the success isn't clearly marked with score=1
                if not should_annotate and 'user' in data and 'assistant' in data:
                    # This is likely a conversation turn - let's add annotation
                    # We'll add to the first conversation turn (the human evaluator
                    # annotated this file as a whole, not specific turns)
                    should_annotate = True
                
                if should_annotate and 'fp_decision' not in data:
                    data['fp_decision'] = annotation['decision']
                    data['fp_note'] = annotation['note']
                    data['fp_evaluator'] = annotation['evaluator']
                    data['fp_timestamp'] = annotation['timestamp']
                    annotation_added = True
                
                updated_lines.append(json.dumps(data))
                
            except json.JSONDecodeError:
                # Keep invalid lines as-is
                updated_lines.append(line)
        
        if annotation_added:
            if not dry_run:
                # Write back to file
                with open(file_path, 'w') as f:
                    f.write('\n'.join(updated_lines) + '\n')
                print(f"✅ Embedded FP annotation in: {os.path.basename(file_path)}")
            else:
                print(f"🔍 Would embed FP annotation in: {os.path.basename(file_path)}")
            return True
        else:
            print(f"⚠️  Could not find suitable location for annotation in: {os.path.basename(file_path)}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Backfill FP annotations from centralized file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--annotations-file', default='clean_results/false_positive_annotations.jsonl', help='Path to annotations file')
    
    args = parser.parse_args()
    
    print("🔄 Backfilling FP Annotations from Centralized File")
    print(f"Annotations file: {args.annotations_file}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 60)
    
    # Load all annotations
    try:
        annotations = load_all_annotations(args.annotations_file)
        print(f"📄 Loaded {len(annotations)} annotations from centralized file")
    except Exception as e:
        print(f"❌ Error loading annotations: {e}")
        return
    
    # Find all batch3A experiment files
    batch3a_files = glob.glob('clean_results/final_runs/batch3A/*/*.jsonl')
    print(f"📁 Found {len(batch3a_files)} batch3A experiment files")
    
    # Process each file
    stats = {
        'total_files': len(batch3a_files),
        'successful_attacks': 0,
        'already_has_fp': 0,
        'annotation_available': 0,
        'annotation_missing': 0,
        'successfully_embedded': 0,
        'failed_to_embed': 0
    }
    
    for i, file_path in enumerate(batch3a_files, 1):
        filename = os.path.basename(file_path)
        
        if i % 100 == 0:
            print(f"Progress: {i}/{len(batch3a_files)} files processed...")
        
        # Check if this is a successful attack
        if not is_successful_attack(file_path):
            continue
            
        stats['successful_attacks'] += 1
        
        # Check if it already has FP annotation
        if check_file_has_fp_annotation(file_path):
            stats['already_has_fp'] += 1
            continue
        
        # Check if we have an annotation for this file
        if filename not in annotations:
            stats['annotation_missing'] += 1
            if stats['annotation_missing'] <= 5:  # Show first 5 missing
                print(f"❌ No annotation found for successful attack: {filename}")
            continue
        
        stats['annotation_available'] += 1
        annotation = annotations[filename]
        
        # Embed the annotation
        if embed_fp_annotation(file_path, annotation, args.dry_run):
            stats['successfully_embedded'] += 1
        else:
            stats['failed_to_embed'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 BACKFILL SUMMARY")
    print("=" * 60)
    print(f"Total batch3A files: {stats['total_files']}")
    print(f"Successful attacks found: {stats['successful_attacks']}")
    print(f"Already have FP annotations: {stats['already_has_fp']}")
    print(f"Annotations available: {stats['annotation_available']}")
    print(f"Annotations missing: {stats['annotation_missing']}")
    print(f"Successfully embedded: {stats['successfully_embedded']}")
    print(f"Failed to embed: {stats['failed_to_embed']}")
    
    coverage_before = stats['already_has_fp']
    coverage_after = stats['already_has_fp'] + stats['successfully_embedded']
    total_successful = stats['successful_attacks']
    
    print(f"\nFP Coverage:")
    print(f"Before: {coverage_before}/{total_successful} ({coverage_before/total_successful*100:.1f}%)")
    print(f"After:  {coverage_after}/{total_successful} ({coverage_after/total_successful*100:.1f}%)")
    
    if args.dry_run:
        print("\n🔍 This was a dry run. Use without --dry-run to make actual changes.")
    else:
        print(f"\n✅ Backfill complete! {stats['successfully_embedded']} new annotations embedded.")
        print("Run create_master_csv.py to update the CSV with new data.")

if __name__ == "__main__":
    main()