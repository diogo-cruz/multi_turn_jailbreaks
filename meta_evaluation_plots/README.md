# Meta-Evaluation Analysis: False Positives and Negatives

This directory contains comprehensive visualizations analyzing the accuracy of the original evaluation system compared to the corrected meta-evaluations.

## 🎯 Key Findings

### Overall Statistics
- **Total files analyzed**: 172 (100 random + 72 human-evaluated from batch3A)
- **False positives**: 68 (39.5%) - Cases marked as jailbroken that weren't
- **False negatives**: 0 (0.0%) - Cases marked as not jailbroken that were
- **Evaluation accuracy**: 59.9%

### 🚨 Critical Issues Identified

1. **High false positive rate**: 39.5% of "successful jailbreaks" were actually failures
2. **No false negatives**: The original evaluator never missed actual jailbreaks
3. **Turn type bias**: Multi-turn conversations have much higher false positive rates (54.9% vs 22.2%)

## 📊 Plot Descriptions

### 1. `tactic_analysis_heatmaps.png`
**Evaluation accuracy by jailbreak tactic and turn type**

- **False Positive Rates by Tactic**:
  - Command: 53.9% (highest)
  - Direct Request: 30.2%
  - Crowding: 29.5%
  - Emotional Appeal: Lowest FP rate

- **Key Insight**: Multi-turn conversations consistently show higher false positive rates across all tactics

### 2. `test_case_analysis_bars.png`
**Error rates by specific test cases (top 15 by sample count)**

- Shows false positive and negative rates for different harmful scenarios
- Demonstrates which types of harmful requests are most prone to evaluation errors
- Separates single-turn vs multi-turn performance

### 3. `model_comparison.png`
**Evaluation accuracy across different target models**

- Compares false positive/negative rates across different LLMs
- Shows which models are most prone to evaluation errors
- Averaged across sufficient sample sizes (≥3 samples per model)

### 4. `overall_summary.png`
**Comprehensive summary of evaluation accuracy**

- **Pie chart**: Overall distribution of correct vs incorrect evaluations
- **Turn type comparison**: Single-turn vs multi-turn error rates
- **Confusion matrix**: Original vs corrected evaluation agreement
- **Issue prevalence**: Most common evaluation problems detected

### 5. `human_ai_comparison.png`
**Human vs AI Meta-Evaluator Agreement Analysis**

- **Agreement Rate by Test Case**: Shows how often human and AI meta-evaluators agree on specific test cases
- **Confusion Matrix**: Compares human decisions (false positive/true positive) with AI issue detection
- **Issue Detection Patterns**: AI confidence scores for different issue types, separated by human classification
- **Overall Agreement**: 53.2% agreement rate between human and AI meta-evaluators (77 overlapping files)

**Key Finding**: Moderate agreement (53.2%) between human and AI meta-evaluators shows some discrepancy in evaluation standards. The main disagreement pattern is that humans mark cases as true positives while AI detects evaluation issues (35 cases), suggesting the AI meta-evaluator may be more sensitive to evaluation problems than human evaluators.

### 6. `rephrasing_impact_analysis.png`
**Impact of Excluding Rephrasing Issues from AI Meta-Evaluator**

- **Agreement Rate Comparison**: Shows current (53.2%) vs modified (75.3%) agreement rates when excluding rephrasing issues
- **Disagreement Breakdown**: Categorizes disagreement cases into rephrasing-only, rephrasing + others, and no rephrasing
- **Test Case Impact**: Identifies which test cases are most affected by rephrasing-only disagreements
- **Tactic Analysis**: Shows distribution of jailbreak tactics in rephrasing disagreements

**Key Finding**: The **22.1 percentage point improvement** (53.2% → 75.3%) when excluding rephrasing issues reveals that the **primary source of human-AI disagreement is philosophical**: whether rephrasing attacks should count as valid jailbreaks. 17 cases would move from disagreement to agreement, showing this is fundamentally a policy question about what constitutes a legitimate jailbreak attack.

## 📊 No-Rephrasing Analysis Plots

To understand the impact of excluding rephrasing issues from the AI meta-evaluator assessment, we've generated comparison versions of all plots with the `_no_rephrasing` suffix:

### 7. `tactic_analysis_heatmaps_no_rephrasing.png`
**Evaluation accuracy by jailbreak tactic (excluding rephrasing issues)**

Shows how false positive rates change when rephrasing is not considered an evaluation problem. Key improvements:
- **Command tactic**: 53.9% → 53.3% FP rate (minimal change)
- **Direct Request**: 30.2% → 24.3% FP rate (significant improvement)
- **Overall accuracy**: 59.9% → 61.6% (+1.7 percentage points)

### 8. `test_case_analysis_bars_no_rephrasing.png`
**Error rates by test case (excluding rephrasing issues)**

Demonstrates which test cases benefit most from excluding rephrasing considerations in evaluation.

### 9. `overall_summary_no_rephrasing.png`
**Comprehensive evaluation accuracy summary (excluding rephrasing issues)**

- **False positives reduced**: 68 → 66 cases (-2)
- **Accuracy improved**: 59.9% → 61.6% (+1.7 points)
- **Turn type gaps persist**: Multi-turn still shows higher error rates than single-turn

### 10. `model_comparison_no_rephrasing.png`
**Model performance comparison (excluding rephrasing issues)**

Shows how different target models' evaluation accuracy changes when rephrasing issues are not penalized.

### 11. `human_ai_comparison_no_rephrasing.png`
**Human vs AI Meta-Evaluator Comparison (excluding rephrasing issues)**

Shows how human-AI agreement changes when the AI meta-evaluator only considers non-rephrasing issues:
- **Agreement rate**: 53.2% → 26.0% (-27.2 percentage points)
- **Surprising result**: Agreement actually decreases when excluding rephrasing
- **Explanation**: Most disagreement cases involve multiple issue types, not just rephrasing alone

**Key Insight**: This reveals that rephrasing issues often co-occur with other evaluation problems. When we remove rephrasing but keep other issues (attacker failure, benign elaboration), we see that humans and AI still disagree significantly, but now the AI finds fewer total issues.

## 🔍 Detailed Analysis

### False Positive Correlation with Issues
Among the 68 false positive cases:
- **100%** had rephrasing issues (attackers made requests innocuous)
- **86.8%** had attacker failure issues (never requested harmful content)
- **47.1%** had benign elaboration issues (models only answered safe parts)
- **14.7%** had multi-step issues
- **1.5%** had soft refusal issues
- **0%** had capability issues

### Turn Type Differences
- **Single-turn**: 22.2% false positive rate, 77.8% accuracy
- **Multi-turn**: 54.9% false positive rate, 44.0% accuracy

**Implication**: The original evaluator significantly struggles with multi-turn conversations, often misinterpreting partial compliance as full jailbreak success.

### Tactic Performance
1. **Command**: Highest false positive rate (53.9%)
2. **Direct Request**: Moderate (30.2%)
3. **Crowding**: Similar to direct request (29.5%)
4. **Emotional Appeal**: Best performing tactic

## 🎯 Implications for Evaluation System

1. **Systematic over-estimation**: The evaluator inflates attack success rates by ~39.5%
2. **Multi-turn vulnerability**: Evaluation accuracy drops dramatically for longer conversations (44% vs 78%)
3. **Issue pattern**: Most false positives result from rephrasing/attacker failure, not genuine model vulnerabilities
4. **Bias direction**: The system errs on the side of marking responses as jailbroken
5. **Human validation**: 53% agreement between human and AI meta-evaluators suggests different evaluation standards, with AI being more sensitive to evaluation issues

## 📈 Recommendations

1. **Improve multi-turn evaluation**: Develop better criteria for assessing partial vs full compliance
2. **Add issue detection**: Incorporate checks for rephrasing and attacker failure
3. **Recalibrate thresholds**: Current system is too permissive in marking jailbreaks as successful
4. **Validation protocol**: Implement regular meta-evaluation to monitor evaluation quality

---

*Generated from 172 files (100 random + 72 human-evaluated) from batch3A using Gemini 2.5 Flash Preview meta-evaluation* 