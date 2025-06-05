
# Reasoning Token Analysis Report

## Dataset Summary
- Total records analyzed: 13,179
- Records with reasoning tokens > 0: 4,626
- Unique models: 1
- Unique test cases: 1

## Key Findings

### Overall Correlations
- **Reasoning Tokens vs Success Rate**: 0.1082
- **Reasoning Tokens vs Success Score**: 0.2440
- **Overall Success Rate**: 19.05%

### Reasoning Token Statistics
- Min reasoning tokens: 0
- Max reasoning tokens: 18025
- Average reasoning tokens: 249.77
- Median reasoning tokens: 0.00

### Success Rate by Reasoning Level
- **High**: 19.27% success rate (avg 353 tokens, n=6589)
- **Low**: 18.96% success rate (avg 111 tokens, n=3296)
- **Medium**: 18.65% success rate (avg 182 tokens, n=3292)
- **None**: 100.00% success rate (avg 0 tokens, n=2)

### Statistical Significance
- T-test (reasoning vs no reasoning): t=-inf, p=nan

### Interpretation
- **Positive correlation**: Higher reasoning token usage is associated with higher success rates
