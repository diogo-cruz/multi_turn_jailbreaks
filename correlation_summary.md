# Correlation Analysis: GPT-4.1-mini vs GPT-4.1-nano Evaluator Scores

## Summary of Findings

We analyzed the correlation between evaluation scores from GPT-4.1-mini (original evaluator) and GPT-4.1-nano for multi-turn jailbreak attempts in batch3A. The analysis revealed:

- **Pearson correlation: -0.1476** (p-value: 0.0003)
- **Spearman rank correlation: -0.1130** (p-value: 0.0059)

The results show a **weak negative correlation** between the two evaluators, which is statistically significant (p < 0.01). This suggests that the two models have somewhat different evaluation standards or criteria when assessing the same AI responses to jailbreak attempts.

## Methodology

Our analysis involved the following steps:

1. Identifying pairs of evaluation files:
   - Original files with scores from GPT-4.1-mini
   - Corresponding re-evaluation files with scores from GPT-4.1-nano (identified by "_eval_gpt-4.1-nano" suffix)

2. Extracting paired scores from both files:
   - Analyzed 216 file pairs from the "crowding" and "direct_request" jailbreak tactics
   - Found 591 valid score pairs (after excluding any non-numeric or "refused" responses)

3. Computing correlation metrics:
   - Pearson correlation coefficient for linear relationship
   - Spearman rank correlation for monotonic relationship
   - Statistical significance testing (p-values)

4. Visualizing the relationship:
   - Scatter plot with regression line
   - Reference diagonal line showing theoretical perfect correlation

## Interpretation

The weak negative correlation suggests that:

1. **Different evaluation criteria**: GPT-4.1-mini and GPT-4.1-nano may be using different criteria or weights when evaluating the harmfulness or appropriateness of responses.

2. **Model size impact**: The smaller size of GPT-4.1-nano may affect its ability to detect subtle nuances in harmful content that GPT-4.1-mini can identify, or vice versa.

3. **Consistency concerns**: The negative correlation raises questions about consistency in AI safety evaluations when using different model sizes.

4. **Statistical significance**: The p-values below 0.01 indicate that this negative correlation is unlikely to be due to random chance.

## Implications

These findings have several implications for AI safety evaluation:

1. **Model choice matters**: The choice of evaluation model can significantly impact the assessment of safety or harmfulness.

2. **Size vs. efficiency tradeoff**: While smaller models like GPT-4.1-nano may be more efficient for evaluations, they may not align with the judgments of larger models.

3. **Need for standardization**: There may be a need for standardized evaluation criteria or benchmarks that work consistently across model sizes.

4. **Human verification**: For critical safety evaluations, human verification might be necessary, given the disagreement between model evaluators.

## Limitations

1. This analysis is limited to two specific jailbreak tactics ("crowding" and "direct_request") and may not generalize to all forms of jailbreak attempts.

2. The scores are discrete values with a limited range, which may affect correlation measurements.

3. We don't have access to the specific prompts or scoring criteria used by each evaluator model.

## Conclusion

The statistically significant negative correlation between GPT-4.1-mini and GPT-4.1-nano evaluator scores highlights the challenges in consistent AI safety evaluation. When designing evaluation pipelines, practitioners should be aware that different model sizes may yield significantly different assessments of the same content. 