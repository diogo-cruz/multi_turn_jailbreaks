#!/usr/bin/env python3
"""
Backfill False Positive Annotations

This script reads annotations from false_positive_annotations.jsonl and embeds them
into the original experiment files where they're missing. It handles both score: 1.0
and score: 1 cases.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import argparse

def load_annotations(annotations_file: str) -> List[Dict]:
    """Load all annotations from the JSONL file."""
    annotations = []
    with open(annotations_file, 'r') as f:
        for line in f:
            if line.strip():
                annotations.append(json.loads(line))
    return annotations

def get_experiment_file_path(annotation: Dict, base_path: str) -> str:
    """Get the full path to the experiment file from annotation data."""
    relative_path = annotation['relative_path']
    filename = annotation['filename']
    return os.path.join(base_path, relative_path, filename)

def check_if_annotation_exists(file_path: str, target_decision: str) -> bool:
    """Check if the file already has FP annotations embedded."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if 'fp_decision' in data and data['fp_decision'] == target_decision:
                        return True
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return False
    
    return False

def embed_annotation_in_file(file_path: str, annotation: Dict, dry_run: bool = False) -> bool:
    """Embed FP annotation into the experiment file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Read all lines
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
                
                # Check if this line should get the annotation
                # Handle both score: 1.0 and score: 1, and other success indicators
                should_annotate = False
                
                if 'score' in data:
                    # Handle numeric scores
                    if data['score'] == 1.0 or data['score'] == 1:
                        should_annotate = True
                    # Handle string scores that represent success
                    elif isinstance(data['score'], str) and data['score'] in ['1.0', '1']:
                        should_annotate = True
                
                # Also check for goal_achieved at the line level
                if data.get('goal_achieved') is True:
                    should_annotate = True
                
                # Special case: for files that might not have clear success indicators,
                # if this is a successful experiment according to annotations, 
                # try to find the most likely successful turn
                if not should_annotate and 'user' in data:
                    # This might be a conversation turn, let's be more lenient
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
                print(f"✅ Embedded annotation in: {os.path.basename(file_path)}")
            else:
                print(f"🔍 Would embed annotation in: {os.path.basename(file_path)}")
            return True
        else:
            print(f"⚠️  No suitable line found for annotation in: {os.path.basename(file_path)}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Backfill FP annotations into experiment files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--base-path', default='clean_results/final_runs', help='Base path for experiment files')
    parser.add_argument('--annotations-file', default='clean_results/false_positive_annotations.jsonl', help='Path to annotations file')
    
    args = parser.parse_args()
    
    print("🔄 Backfilling False Positive Annotations")
    print(f"Base path: {args.base_path}")
    print(f"Annotations file: {args.annotations_file}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 50)
    
    # Load annotations
    try:
        annotations = load_annotations(args.annotations_file)
        print(f"📄 Loaded {len(annotations)} annotations")
    except Exception as e:
        print(f"❌ Error loading annotations: {e}")
        return
    
    # Process each annotation
    stats = {
        'total': len(annotations),
        'already_embedded': 0,
        'successfully_embedded': 0,
        'failed': 0,
        'file_not_found': 0
    }
    
    for i, annotation in enumerate(annotations, 1):
        print(f"\n[{i}/{len(annotations)}] Processing: {annotation['filename']}")
        
        # Get file path
        file_path = get_experiment_file_path(annotation, args.base_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            stats['file_not_found'] += 1
            continue
        
        # Check if annotation already exists
        if check_if_annotation_exists(file_path, annotation['decision']):
            print(f"✅ Annotation already exists in: {os.path.basename(file_path)}")
            stats['already_embedded'] += 1
            continue
        
        # Embed the annotation
        if embed_annotation_in_file(file_path, annotation, args.dry_run):
            stats['successfully_embedded'] += 1
        else:
            stats['failed'] += 1
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 BACKFILL SUMMARY")
    print("=" * 50)
    print(f"Total annotations: {stats['total']}")
    print(f"Already embedded: {stats['already_embedded']}")
    print(f"Successfully embedded: {stats['successfully_embedded']}")
    print(f"Failed to embed: {stats['failed']}")
    print(f"File not found: {stats['file_not_found']}")
    
    if args.dry_run:
        print("\n🔍 This was a dry run. Use --no-dry-run to make actual changes.")
    else:
        print(f"\n✅ Backfill complete! {stats['successfully_embedded']} annotations embedded.")

if __name__ == "__main__":
    main()