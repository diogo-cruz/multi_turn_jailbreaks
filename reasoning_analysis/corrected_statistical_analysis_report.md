
# Corrected Statistical Analysis Report - Batch Thinking + Direct Request

## Dataset Overview
- **Single-Turn Conversations**: 267
- **Multi-Turn Conversations**: 271
- **Total Conversations**: 538

## Corrected Score Computation
- **Method**: Maximum score across all rounds per JSONL file
- **Rationale**: Each JSONL represents one test case; we want the best performance achieved

## Key Statistical Findings

### Descriptive Statistics

**Single-Turn (n=267):**
- Mean max score: 0.526 (SD=0.443)
- Success rate: 30.7%
- Mean reasoning tokens: 482.6 (SD=673.2)

**Multi-Turn (n=271):**
- Mean max score: 0.676 (SD=0.422)
- Success rate: 51.3%
- Mean reasoning tokens: 460.1 (SD=617.5)

### Multi-Turn Advantage
- **Score difference**: +0.150 (multi-turn higher)
- **Success rate difference**: +20.6% (multi-turn higher)

### Correlation Analysis
- **Single-Turn**: Reasoning tokens vs max score = 0.2149
- **Multi-Turn**: Reasoning tokens vs max score = 0.1232

### Statistical Significance Tests
- **T-test** (single vs multi-turn scores): t=-4.0328, p=0.0001
- **Effect size** (Cohen's d): 0.3477
- **Effect size interpretation**: small
