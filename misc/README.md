# Analysis Scripts and Files

This directory contains analysis scripts and intermediate files created during the evaluation mismatch investigation.

## Analysis Scripts

- `test_goal_score_mismatch.py` - Main script that identified the 1,121 files with evaluation mismatches
- `analyze_evaluation_mismatches_by_directory.py` - Analyzes mismatch patterns by batch directory
- `analyze_summary_entries_by_batch.py` - Identifies which batches have summary entries vs clean format
- `create_mismatch_cards.py` - Creates detailed CSV analysis of all mismatch files
- `analyze_edge_cases.py` - Investigates specific edge cases and patterns
- `analyze_batch3a_pairs.py` - Compares paired single/multi-turn results in batch3A
- `create_master_csv.py` - Creates master CSV for model comparison analysis
- `count_model_data.py` - Counts data availability by model
- `debug_matching.py` - Debug script for investigating matching patterns
- `edge_case_summary.py` - Summarizes edge case findings
- `find_edge_cases.py` - Searches for edge cases in the data
- `investigate_file_format.py` - Investigates file format inconsistencies

## Output Files

- `mismatch_analysis_summary.md` - Summary of the evaluation mismatch investigation findings
- `edge_case_investigation_report.md` - Detailed report on edge cases and patterns
- `batch3a_paired_results.csv` - Paired analysis results for batch3A
- `model_comparison.csv` - Model-by-model comparison data
- `edge_cases_analysis.json` - JSON data for edge case analysis
- `mismatch_cards_detailed.csv` - Comprehensive CSV with all 1,121 mismatch files and their metadata

## Key Finding

**Root Cause**: Commit `ce69f38a` on May 6, 2025 introduced the `write_output_data()` function that creates summary entries with separate evaluations, which can disagree with conversation round evaluations.

**Impact**: 1,121 files (16% of successful jailbreaks) have `goal_achieved: true` but no `score: 1.0` in conversation rounds.

## Usage

Run scripts from within the `misc/` directory:
```bash
cd misc/
python test_goal_score_mismatch.py
python analyze_summary_entries_by_batch.py
```

All scripts use relative paths (`../clean_results/final_runs/`) to access the data directory.