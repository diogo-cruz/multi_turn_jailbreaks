# Reasoning Token Analysis

This folder contains analysis scripts and visualizations for studying the relationship between reasoning token usage and jailbreak success rates in multi-turn conversations.

## Files

### Main Analysis Scripts

1. **`multiturn_min_score_analysis.py`** - **Primary analysis script**
   - Comprehensive multi-turn analysis with 6 visualizations
   - Analyzes correlation between reasoning tokens and maximum scores
   - Fixed token range analysis (0-400, 400-800, 800-1200, 1200-1600, 1600+)
   - Generates dual y-axis plot showing both success rates and average max scores
   - **Usage**: `python multiturn_min_score_analysis.py`

2. **`simple_reasoning_analysis.py`** - Turn-level analysis (initial approach)
   - Treats each turn individually rather than conversation-level aggregation
   - 4-panel visualization
   - **Usage**: `python simple_reasoning_analysis.py`

3. **`reasoning_analysis_conversation_level.py`** - Conversation-level aggregation
   - Intermediate analysis that properly aggregates by conversation
   - Uses final success outcomes for each conversation
   - **Usage**: `python reasoning_analysis_conversation_level.py`

4. **`reasoning_token_analysis.py`** - Advanced analysis with statistical tests
   - Comprehensive analysis with seaborn visualizations
   - Statistical significance testing
   - Model-by-model breakdown
   - **Usage**: `python reasoning_token_analysis.py`

### Key Findings

**Dataset**: 1,102 multi-turn conversations (filtered, outliers > 10,000 tokens removed)

**Fixed Token Ranges Analysis**:
| Token Range | Success Rate | Avg Max Score | Sample Size |
|-------------|--------------|---------------|-------------|
| 0-400       | 42.7%        | 0.566         | 694         |
| 400-800     | 28.2%        | 0.494         | 188         |
| 800-1200    | 36.9%        | 0.573         | 103         |
| 1200-1600   | 31.6%        | 0.634         | 57          |
| 1600+       | 58.3%        | 0.802         | 60          |

**Key Insights**:
1. **U-shaped relationship**: Both minimal reasoning (0-400) and extensive reasoning (1600+) outperform moderate reasoning
2. **Performance valley**: 400-800 token range shows poorest performance across all metrics
3. **Peak performance**: 1600+ tokens achieve highest success rate (58.3%) and average max score (0.802)
4. **Weak overall correlation**: 0.0957 between avg reasoning tokens and max scores

## Requirements

```bash
pip install pandas numpy matplotlib seaborn pathlib
```

## Data Source

All scripts read from `../clean_results/final_runs/batch_thinking/` which contains:
- 1,109 multi-turn JSONL files
- 1,108 single-turn JSONL files
- Each file represents one jailbreak conversation
- Contains reasoning token usage and success metrics

## Usage

From the `reasoning_analysis/` directory:

```bash
# Run the main comprehensive analysis
python multiturn_min_score_analysis.py

# Run other analyses
python simple_reasoning_analysis.py
python reasoning_analysis_conversation_level.py
python reasoning_token_analysis.py
```

All scripts will automatically find the data in the parent directory and generate visualizations in the current folder.

## Note

The analysis scripts were moved to this dedicated folder to keep the project root clean. All import paths have been updated to correctly reference the data directory from this location.