#!/usr/bin/env python3
"""
Fixed Backfill Script for FP Annotations

This script properly maps annotations from false_positive_annotations.jsonl
to the actual experiment files using both relative_path and filename.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import argparse

def load_annotations_properly(annotations_file: str) -> List[Dict]:
    """Load all annotations with full path mapping."""
    annotations = []
    with open(annotations_file, 'r') as f:
        for line in f:
            if line.strip():
                ann = json.loads(line)
                # Construct full file path
                ann['full_path'] = os.path.join('clean_results/final_runs', ann['relative_path'], ann['filename'])
                annotations.append(ann)
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

def embed_fp_annotation(file_path: str, annotation: Dict, dry_run: bool = False) -> bool:
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
                should_annotate = False
                
                # For successful attacks (goal_achieved=True or score=1.0/1)
                if data.get('goal_achieved') is True:
                    should_annotate = True
                elif 'score' in data and (data['score'] == 1.0 or data['score'] == 1):
                    should_annotate = True
                
                # Add annotation to successful lines that don't already have it
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
            print(f"⚠️  No suitable location for annotation in: {os.path.basename(file_path)}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fixed backfill FP annotations')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--annotations-file', default='clean_results/false_positive_annotations.jsonl', help='Path to annotations file')
    
    args = parser.parse_args()
    
    print("🔄 Fixed Backfill Process Starting")
    print(f"Annotations file: {args.annotations_file}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 60)
    
    # Load annotations properly
    try:
        annotations = load_annotations_properly(args.annotations_file)
        print(f"📄 Loaded {len(annotations)} annotations from centralized file")
    except Exception as e:
        print(f"❌ Error loading annotations: {e}")
        return
    
    # Process each annotation
    stats = {
        'total_annotations': len(annotations),
        'file_not_found': 0,
        'already_has_fp': 0,
        'successfully_embedded': 0,
        'failed_to_embed': 0
    }
    
    for i, annotation in enumerate(annotations, 1):
        file_path = annotation['full_path']
        filename = annotation['filename']
        
        if i % 50 == 0:
            print(f"Progress: {i}/{len(annotations)} annotations processed...")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            stats['file_not_found'] += 1
            continue
        
        # Check if it already has FP annotation
        if check_file_has_fp_annotation(file_path):
            stats['already_has_fp'] += 1
            continue
        
        # Embed the annotation
        if embed_fp_annotation(file_path, annotation, args.dry_run):
            stats['successfully_embedded'] += 1
        else:
            stats['failed_to_embed'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 FIXED BACKFILL SUMMARY")
    print("=" * 60)
    print(f"Total annotations: {stats['total_annotations']}")
    print(f"Files not found: {stats['file_not_found']}")
    print(f"Already have FP annotations: {stats['already_has_fp']}")
    print(f"Successfully embedded: {stats['successfully_embedded']}")
    print(f"Failed to embed: {stats['failed_to_embed']}")
    
    if args.dry_run:
        print("\n🔍 This was a dry run. Use without --dry-run to make actual changes.")
    else:
        print(f"\n✅ Fixed backfill complete! {stats['successfully_embedded']} new annotations embedded.")
        print("Run create_master_csv.py to update the CSV with new data.")

if __name__ == "__main__":
    main()