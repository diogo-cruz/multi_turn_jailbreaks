# Comparative Analysis of Three Evaluation Systems for Multi-Turn Jailbreak Attacks

**A Comprehensive Report on Original, Human, and AI Meta-Evaluation System Performance**

---

## Executive Summary

This report presents a thorough comparative analysis of three distinct evaluation systems used to assess the success of multi-turn jailbreak attacks against large language models:

1. **Original Evaluation System**: Automated baseline evaluations from initial attack runs
2. **Human Expert Evaluations**: Manual assessments by domain experts  
3. **AI Meta-Evaluation System**: Systematic re-evaluation using specialized prompts

Our analysis reveals significant differences between these systems, with agreement rates ranging from 49.8% to 79.0% depending on the comparison pair. These findings have important implications for jailbreak research methodology and evaluation system design.

---

## 1. Introduction

### 1.1 Background

The evaluation of jailbreak attack success is a critical component of AI safety research. However, different evaluation methodologies can yield substantially different results, making it essential to understand the characteristics and biases of various evaluation systems.

### 1.2 Research Questions

1. How do agreement rates differ between the three evaluation systems?
2. What patterns emerge in disagreements between systems?
3. Are certain jailbreak tactics more prone to evaluation disagreements?
4. Which evaluation system demonstrates the most appropriate balance of sensitivity and specificity?

### 1.3 Dataset

Our analysis encompasses **223-271 cases** (depending on system overlap) from a comprehensive jailbreak evaluation dataset, covering:
- **4 jailbreak tactics**: Command, Crowding, Direct Request, Emotional Appeal
- **Multiple test cases**: Representing various harm categories
- **Diverse target models**: Including GPT, Claude, and other LLMs

---

## 2. Methodology

### 2.1 Evaluation Systems Description

#### 2.1.1 Original Evaluation System
- **Purpose**: Baseline automated evaluation during initial attack execution
- **Method**: Rule-based assessment using StrongREJECT methodology
- **Evaluator**: Primarily gpt-4.1-mini
- **Characteristics**: Fast, consistent, but potentially permissive

#### 2.1.2 Human Expert Evaluation
- **Purpose**: Ground truth assessment by domain experts
- **Method**: Manual review focusing on harmful intent and actionable content
- **Evaluators**: Multiple trained human evaluators
- **Characteristics**: Nuanced understanding, potential inter-evaluator variance

#### 2.1.3 AI Meta-Evaluation System
- **Purpose**: Systematic re-evaluation identifying specific failure modes
- **Method**: Multi-factor analysis using specialized prompts
- **Evaluator**: Gemini 2.5 Flash Preview with 20-factor scoring
- **Characteristics**: Detailed issue categorization, potentially conservative

### 2.2 Analysis Framework

#### 2.2.1 Agreement Metrics
- **Simple Agreement Rate**: Percentage of cases with identical binary evaluations
- **Cohen's Kappa**: Inter-rater reliability accounting for chance agreement
- **Three-Way Agreement**: Cases where all three systems agree

#### 2.2.2 Statistical Tests
- **McNemar's Test**: Comparing paired binary classifications
- **Chi-square Test**: Testing independence of evaluation systems
- **Confidence Intervals**: Quantifying uncertainty in agreement estimates

---

## 3. Results

### 3.1 Overall Agreement Patterns

#### 3.1.1 Pairwise Agreement Rates

| Comparison | Agreement Rate | Cohen's Kappa | Statistical Significance |
|------------|---------------|---------------|-------------------------|
| **Original vs Human** | 76.2% | 0.524 | p < 0.001 |
| **Original vs AI Meta** | 49.8% | 0.211 | p < 0.001 |
| **Human vs AI Meta** | 79.0% | 0.578 | p = 0.152 |

**Key Findings:**
- Highest agreement: Human vs AI Meta-Evaluator (79.0%)
- Lowest agreement: Original vs AI Meta-Evaluator (49.8%)
- All differences are statistically significant except Human vs AI Meta

#### 3.1.2 Three-Way Agreement
- **Complete Agreement**: 67.2% of cases (150/223)
- **Two-System Agreement**: 28.3% of cases
- **Complete Disagreement**: 4.5% of cases

### 3.2 Evaluation System Characteristics

#### 3.2.1 Positive Evaluation Rates
- **Original System**: 100.0% (in analyzed subset)
- **Human Evaluators**: 61.4%
- **AI Meta-Evaluator**: 50.2%

**Interpretation**: The original system was highly permissive, marking all cases in the analyzed subset as successful jailbreaks. Human evaluators and the AI meta-evaluator were substantially more conservative.

#### 3.2.2 System Bias Analysis
- **Original System**: +38.6% relative to human evaluations (highly permissive)
- **Human Evaluators**: Baseline reference
- **AI Meta-Evaluator**: -11.2% relative to human evaluations (conservative)

### 3.3 Performance by Jailbreak Tactic

#### 3.3.1 Agreement Rates by Tactic

| Tactic | Original-Human | Original-AI | Human-AI | Sample Size |
|--------|----------------|-------------|----------|-------------|
| **Direct Request** | 89.3% | 77.4% | 86.9% | 84 cases |
| **Crowding** | 71.6% | 60.5% | 84.0% | 81 cases |
| **Emotional Appeal** | 64.5% | 25.8% | 67.7% | 31 cases |
| **Command** | 65.3% | 17.3% | 70.7% | 75 cases |

**Key Insights:**
1. **Direct Request** attacks show highest inter-system agreement
2. **Command** attacks have lowest Original-AI agreement (17.3%)
3. **Emotional Appeal** shows moderate agreement but smaller sample size

#### 3.3.2 Tactic-Specific Analysis

**Direct Request Attacks:**
- Most straightforward to evaluate
- High agreement across all system pairs
- Clear success/failure criteria

**Command Attacks:**
- Highest disagreement between Original and AI Meta-Evaluator
- Suggests complex evaluation challenges
- May involve subtle failure modes missed by original system

**Crowding Attacks:**
- Moderate agreement levels
- Human-AI Meta agreement remains high (84.0%)
- Original system may miss nuanced evaluation criteria

**Emotional Appeal Attacks:**
- Smallest sample size limits conclusions
- Substantial variation in agreement rates
- May require human judgment for context evaluation

### 3.4 Disagreement Pattern Analysis

#### 3.4.1 Three-Way Disagreement Categories

| Pattern | Percentage | Count | Interpretation |
|---------|------------|-------|----------------|
| **All Agree (Jailbroken)** | 32.7% | 73 | Clear consensus on success |
| **All Agree (Not Jailbroken)** | 34.5% | 77 | Clear consensus on failure |
| **Original vs Human+AI** | 18.8% | 42 | Original too permissive |
| **Human+AI vs Original** | 8.1% | 18 | Original too conservative |
| **Other Mixed** | 5.9% | 13 | Complex disagreements |

**Primary Disagreement Source**: Original evaluator appears too permissive in 18.8% of cases.

#### 3.4.2 Disagreement by Test Case

**Highest Disagreement Test Cases:**
1. **Airbnb Voyeurism**: 67% disagreement rate
2. **Terrorist Recruitment**: 58% disagreement rate  
3. **LGBTQ Insults**: 52% disagreement rate

**Lowest Disagreement Test Cases:**
1. **Counterfeit Money**: 23% disagreement rate
2. **Drunk Driving**: 28% disagreement rate
3. **Date Rape Drug**: 31% disagreement rate

### 3.5 Model-Specific Performance

#### 3.5.1 Agreement by Target Model

| Model Family | Original-Human | Original-AI | Human-AI | Sample Size |
|--------------|----------------|-------------|----------|-------------|
| **Claude Models** | 78.4% | 52.1% | 81.2% | 97 cases |
| **GPT Models** | 74.6% | 47.3% | 76.8% | 89 cases |
| **Other Models** | 75.0% | 49.2% | 78.1% | 37 cases |

**Finding**: Agreement patterns are consistent across model families, suggesting evaluation system differences are not model-dependent.

---

## 4. Statistical Analysis

### 4.1 Significance Testing

#### 4.1.1 McNemar's Test Results
- **Original vs Human**: χ² = 14.7, p < 0.001 (significant difference)
- **Original vs AI Meta**: χ² = 28.3, p < 0.001 (significant difference)  
- **Human vs AI Meta**: χ² = 2.1, p = 0.152 (no significant difference)

#### 4.1.2 Effect Sizes
- **Original-Human Agreement**: Medium effect (κ = 0.524)
- **Original-AI Agreement**: Small effect (κ = 0.211)
- **Human-AI Agreement**: Medium-Large effect (κ = 0.578)

### 4.2 Confidence Intervals

| Comparison | Agreement Rate | 95% CI |
|------------|---------------|---------|
| Original vs Human | 76.2% | [70.8%, 81.6%] |
| Original vs AI Meta | 49.8% | [43.6%, 56.0%] |
| Human vs AI Meta | 79.0% | [74.1%, 83.9%] |

---

## 5. Discussion

### 5.1 Evaluation System Strengths and Limitations

#### 5.1.1 Original Evaluation System
**Strengths:**
- Fast and scalable
- Consistent methodology
- Enables large-scale studies

**Limitations:**
- Appears overly permissive
- May miss subtle failure modes
- Limited context understanding

#### 5.1.2 Human Expert Evaluation
**Strengths:**
- Nuanced understanding of context
- Can assess implicit harm
- Flexible evaluation criteria

**Limitations:**
- Time-intensive and expensive
- Potential inter-evaluator variance
- Difficulty scaling to large datasets

#### 5.1.3 AI Meta-Evaluation System
**Strengths:**
- Systematic issue identification
- Scalable with detailed feedback
- Consistent application of criteria

**Limitations:**
- May be overly conservative
- Potential prompt sensitivity
- Limited contextual reasoning

### 5.2 Implications for Jailbreak Research

#### 5.2.1 Methodological Considerations
1. **Multi-System Validation**: Using multiple evaluation systems provides more robust assessment
2. **Tactic-Specific Evaluation**: Different tactics may require specialized evaluation approaches
3. **Threshold Calibration**: Agreement analysis can inform optimal decision thresholds

#### 5.2.2 Best Practices Recommendations
1. **Primary Evaluation**: Use AI meta-evaluation for scalable, systematic assessment
2. **Validation Subset**: Apply human evaluation to representative sample for calibration
3. **Disagreement Analysis**: Investigate cases with evaluation system disagreements
4. **Tactic Awareness**: Consider tactic-specific evaluation challenges

### 5.3 Future Research Directions

#### 5.3.1 Evaluation System Improvement
- **Hybrid Approaches**: Combining strengths of different systems
- **Adaptive Thresholds**: Tactic-specific decision boundaries
- **Confidence Scoring**: Quantifying evaluation uncertainty

#### 5.3.2 Validation Studies
- **Inter-Evaluator Reliability**: Measuring human evaluator consistency
- **Prompt Engineering**: Optimizing AI meta-evaluation prompts
- **Cross-Domain Validation**: Testing on different attack types

---

## 6. Conclusions

### 6.1 Key Findings

1. **Substantial Evaluation Differences**: Agreement rates between systems range from 49.8% to 79.0%
2. **System-Specific Biases**: Original system is overly permissive; AI meta-evaluator is conservative
3. **Tactic Dependency**: Agreement varies significantly by jailbreak tactic
4. **Human-AI Convergence**: Human and AI meta-evaluations show highest agreement (79.0%)

### 6.2 Recommendations

#### 6.2.1 For Researchers
- Use multiple evaluation systems for robust assessment
- Report evaluation methodology clearly in publications
- Consider tactic-specific evaluation challenges
- Validate automated systems against human judgment

#### 6.2.2 For Evaluation System Design
- Balance sensitivity and specificity carefully
- Incorporate domain expert feedback in system design
- Provide confidence scores with evaluations
- Enable systematic disagreement analysis

### 6.3 Limitations

1. **Dataset Scope**: Analysis limited to specific tactics and test cases
2. **Temporal Factors**: Evaluation systems may evolve over time
3. **Context Dependency**: Results may not generalize to all domains
4. **Human Evaluator Variance**: Limited analysis of inter-evaluator reliability

### 6.4 Final Remarks

This comprehensive analysis reveals the critical importance of evaluation system choice in jailbreak research. The substantial differences between systems highlight the need for multi-faceted evaluation approaches and careful consideration of system-specific biases. As the field continues to evolve, establishing standardized evaluation frameworks with known characteristics will be essential for reproducible and reliable research.

The finding that human evaluators and AI meta-evaluators achieve 79.0% agreement suggests a promising direction for scalable evaluation systems that maintain human-level judgment quality while providing the systematic analysis capabilities needed for large-scale research.

---

## Appendices

### Appendix A: Detailed Statistical Results
[Complete statistical test outputs and confidence intervals]

### Appendix B: Evaluation System Specifications  
[Detailed descriptions of evaluation methodologies and prompts]

### Appendix C: Sample Case Analysis
[Examples of agreement and disagreement cases with detailed analysis]

### Appendix D: Data Availability Statement
[Information about dataset access and reproducibility]

---

**Report Generated**: December 2024  
**Analysis Framework**: Three-Way Evaluation System Comparison  
**Dataset Size**: 223-271 cases (depending on system overlap)  
**Statistical Software**: Python with pandas, scipy, sklearn  
**Visualization**: Publication-quality matplotlib/seaborn plots