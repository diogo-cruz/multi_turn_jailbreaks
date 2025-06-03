# Human TODO: Data Issues to Fix

## Overview
The plotting scripts are missing significant amounts of data due to incomplete model information. This document outlines what needs to be added to the data files to get complete plot coverage.

## Issues Identified

### 1. Missing Models in `model_comparison.csv`

The following **15 models** from experimental data are missing from `model_comparison.csv` and need to be added:

#### Anthropic Models
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3.7-sonnet` 
- `anthropic/claude-3.7-sonnet:thinking`

#### Google Models
- `google/gemini-2.5-flash-preview`
- `google/gemini-2.5-pro-preview`
- `google/gemini-2.5-pro-preview-03-25`

#### OpenAI Models
- `openai/gpt-4.1`
- `openai/gpt-4.1-mini`
- `openai/gpt-4.1-nano`
- `openai/gpt-4o`
- `openai/o1-mini`
- `openai/o3-mini`
- `openai/o4-mini`

#### Qwen Models
- `qwen/qwen3-14b`
- `qwen/qwen3-8b`

### 2. Model Name Matching Issues

Some models in `model_comparison.csv` use different naming conventions than in the experimental data:

#### Models that need exact name matching:
- **Experimental**: `deepseek/deepseek-r1` → **model_comparison.csv**: `DeepSeek-R1`
- **Experimental**: `qwen/qwen-2.5-72b-instruct` → **model_comparison.csv**: `Qwen-2.5-72B`
- **Experimental**: `qwen/qwen-2.5-7b-instruct` → **model_comparison.csv**: `Qwen-2.5-7B`

**Recommended Fix**: Either:
1. Update `model_comparison.csv` to use the same naming convention as experimental data, OR
2. Add a "Experimental_Name" column to `model_comparison.csv` for mapping

### 3. Sparse Reasoning Data

**Issue**: Only 631 out of 14,173 experimental records (4.5%) have reasoning level data (most are NaN).

**Impact**: The ASR vs Reasoning plot has very limited data.

**Recommendation**: Fill in reasoning levels for more experimental runs, or document that this analysis is limited to the subset with reasoning data.

## Required Information for Missing Models

For each missing model, please add the following columns to `model_comparison.csv`:

| Column | Description | Example |
|--------|-------------|---------|
| Model | Exact model name from experimental data | `anthropic/claude-3.5-sonnet` |
| Company | Model creator/company | `Anthropic` |
| Release Date | When the model was released | `June 2024` |
| Parameters | Number of parameters (in billions) | `100.0` |
| Parameter Accuracy | How accurate the parameter count is | `estimate` or `exact` |
| Activated Parameters | Active parameters (for MoE models) | `100.0` |
| Context Length | Maximum context window | `200K` |
| Architecture | Model architecture type | `Transformer-based` |
| Training Data | Brief description of training data | `Diverse corpus with RLHF` |
| Key Features | Notable model features | `Enhanced reasoning capabilities` |
| Benchmarks | Performance highlights | `Strong performance on reasoning tasks` |

## Current Plot Coverage After Fixes

### Before Fixes:
- **Model Size Plot**: 41/42 models (97.6%) - many incorrect matches
- **Release Date Plot**: Similar coverage issues
- **Reasoning Plot**: Limited to 631 data points (4.5% of total)

### After Fixes Would Provide:
- **Model Size Plot**: 42/42 models (100%) - all correct matches
- **Release Date Plot**: 42/42 models (100%) - all correct matches  
- **Reasoning Plot**: Still limited by sparse reasoning data in experimental results
- **Tactics Plot**: Already complete (no model metadata needed)

## Priority

**High Priority**: Add the 15 missing models to `model_comparison.csv` with at least Model name, Parameters, and Release Date.

**Medium Priority**: Fix naming consistency between files.

**Low Priority**: Fill in reasoning data (if feasible) or document the limitation.

## Verification

After making changes, run:
```bash
cd paper_plots/src
python generate_all_plots.py
```

The scripts will automatically use any additional model data that becomes available. 