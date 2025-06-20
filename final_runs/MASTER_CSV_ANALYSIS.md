# Master CSV Analysis Results

Generated from `csv_results/master_results_verified.csv` containing **13,580 total experiments**

## Summary Statistics

- **Total experiments**: 13,580 (reduced by 10 after moving unverified model results)
- **Unique batches**: 8
- **Unique models**: 37 (reduced from 39 after removing unverified models)
- **Unique test cases**: 30 (reduced from 32)
- **Unique tactics**: 7

## Changes Made

**Moved to unverified directory** (`clean_results/final_runs_have_some_issues/batch2D_2_unverified/`):
- **deepseek-r1**: 7 experiments (remove_watermarks experiments)
- **o3-mini**: 2 experiments (academic_integrity experiments) 
- **claude-3.7-sonnet:thinking**: 1 experiment (extremist_content experiment)

This resulted in **batch2D_2** being reduced from 330 to 320 experiments, containing only verified `llama-3.1-70b-instruct` and `llama-3.1-8b-instruct` results.

## Batch Distribution

| Batch | Total Experiments |
|-------|------------------|
| batch_1 | 3,249 |
| batch2B | 1,675 |
| batch_thinking | 1,283 |
| batch3A | 518 |
| batch2D | 215 |
| batch2D_2 | 195 (reduced from 205 after moving unverified models) |
| batch2C | 169 |
| batch3A_additional | 118 |

## Results by Batch and Model

### BATCH_1 (3,249 experiments)
- gpt-4o-mini-2024-07-18: 990
- llama-3.1-405b-instruct: 990
- llama-3.1-70b-instruct: 990
- llama-3.1-8b-instruct: 990
- llama-3.2-1b-instruct: 990
- llama-3.2-3b-instruct: 990
- llama-3.3-70b-instruct: 990

### BATCH2B (1,675 experiments)
- claude-3-haiku: 160
- deepseek-chat-v3-0324: 160
- gemini-2.0-flash-001: 160
- gemini-2.0-flash-lite-001: 160
- gemini-flash-1.5: 160
- gemma-2-9b-it: 160
- gemma-3-12b-it: 160
- gemma-3-27b-it: 160
- grok-3-mini-beta: 160
- llama-4-maverick: 160
- llama-4-scout: 160
- mistral-7b-instruct-v0.3: 160
- mistral-nemo: 160
- mistral-small-3.1-24b-instruct: 160
- mistral-tiny: 160
- qwen-2.5-72b-instruct: 160
- qwen-2.5-7b-instruct: 160

### BATCH_THINKING (1,283 experiments)
- claude-3.7-sonnet: 317
- gemini-2.5-flash-preview: 317
- gemini-2.5-pro-preview: 315
- o1-mini: 318
- o3-mini: 317
- o4-mini: 318
- qwen3-8b: 315

### BATCH3A (518 experiments)
- claude-3.5-sonnet: 80
- claude-3.7-sonnet: 81
- deepseek-chat-v3-0324: 79
- gemini-2.5-flash-preview: 80
- gemini-2.5-pro-preview-03-25: 80
- gpt-4.1: 80
- gpt-4.1-mini: 80
- gpt-4.1-nano: 80
- gpt-4o: 80

### BATCH2D (215 experiments)
- llama-3.1-70b-instruct: 160
- llama-3.1-8b-instruct: 160

### BATCH2D_2 (195 experiments) - **VERIFIED MODELS ONLY**
- llama-3.1-70b-instruct: 160
- llama-3.1-8b-instruct: 160

*Note: deepseek-r1 (7), o3-mini (2), and claude-3.7-sonnet:thinking (1) experiments moved to unverified directory*

### BATCH2C (169 experiments)
- llama-3.1-70b-instruct: 86
- llama-3.1-8b-instruct: 87

### BATCH3A_ADDITIONAL (118 experiments)
- claude-3.5-sonnet: 20
- claude-3.7-sonnet: 20
- deepseek-chat-v3-0324: 20
- gemini-2.5-flash-preview: 20
- gemini-2.5-pro-preview-03-25: 20
- gpt-4.1: 20
- gpt-4.1-mini: 20
- gpt-4.1-nano: 20
- gpt-4o: 20

## Top Models Across All Batches

1. llama-3.1-8b-instruct: 1,397
2. llama-3.1-70b-instruct: 1,396
3. gpt-4o-mini-2024-07-18: 990
4. llama-3.2-3b-instruct: 990
5. llama-3.3-70b-instruct: 990
6. llama-3.1-405b-instruct: 990
7. llama-3.2-1b-instruct: 990
8. claude-3.7-sonnet: 418
9. gemini-2.5-flash-preview: 417
10. o1-mini: 318

## Top Test Cases Across All Batches

1. terrorist_recruitment: 703
2. airbnb_voyeurism: 700
3. lgbtq_insults: 700
4. pistol_serial_numbers: 698
5. date_rape_drug: 698
6. drunk_driving: 698
7. fake_online_profile: 697
8. false_accusation: 697
9. remove_watermarks: 697 (reduced from 704 after removing unverified models)
10. counterfeit_money: 695

## Top Tactics Across All Batches

1. direct_request: 3,125 (reduced from 3,135 after removing unverified models)
2. emotional_appeal: 2,890
3. crowding: 2,839
4. command: 2,836
5. actor_attack: 630
6. opposite_day: 630
7. crescendomation: 630

## Test Case + Tactic Combinations by Batch

### BATCH_1 Pattern
- Most systematic with 42 experiments per tactic-testcase combination for main tactics
- 21 experiments per combination for specialized tactics (actor_attack, opposite_day, crescendomation)
- Covers 30 test cases × 6 tactics comprehensively

### BATCH2B Pattern  
- Consistent 34 experiments per tactic-testcase combination
- Covers 20 test cases × 4 tactics (command, crowding, direct_request, emotional_appeal)

### BATCH_THINKING Pattern
- Generally 56 experiments per combination with some variation (50-56 range)
- Covers 10 test cases × 4 tactics

### BATCH3A Pattern
- Consistent 18 experiments per combination 
- Covers 10 test cases × 4 tactics
- One anomaly: crowding + lgbtq_insults has 19 experiments

### BATCH3A_ADDITIONAL Pattern
- Consistent 18 experiments per combination
- Only direct_request tactic
- Covers 10 additional test cases not in main batch3A

### Smaller Batches (BATCH2C, BATCH2D, BATCH2D_2)
- Generally 4 experiments per combination
- More focused subsets of test cases and tactics
- **BATCH2D_2 now contains only verified llama models**

## Files Generated

- `csv_results/master_results_verified.csv` - Main verified dataset
- `csv_results/batch_model_breakdown.csv` - Detailed breakdown by batch and model
- `csv_results/batch_combo_breakdown.csv` - Detailed breakdown by batch and tactic+testcase combinations

## Unverified Models (Moved)

The following experimental results were moved to `clean_results/final_runs_have_some_issues/batch2D_2_unverified/`:
- **deepseek-r1**: 7 remove_watermarks experiments
- **o3-mini**: 2 academic_integrity experiments  
- **claude-3.7-sonnet:thinking**: 1 extremist_content experiment

These models were moved due to verification concerns and are excluded from the main analysis.

---

*Analysis updated on 2025-06-20 after moving unverified models using `misc/analyze_master_csv.py`*