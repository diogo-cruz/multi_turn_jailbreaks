# Research Logbook

This file tracks major changes, experiments, and development milestones in the Multi-Turn Jailbreaks repository.

## 📝 Usage Guidelines

- **Update this file** whenever making major changes to the codebase or running significant experiments
- **Include timestamps** for all entries
- **Focus on research insights** and major developments, not detailed code changes (git commits handle that)
- **Describe experimental findings** and their implications
- **Note system changes** that affect future work

---

## 2025-06-21 - Repository Documentation Enhancement

### 📚 Logbook System Implementation
**Author**: Claude Code Assistant  
**Impact**: Improved research tracking and documentation consistency

#### Documentation Structure
- **Created** `LOGBOOK.md` - Research milestone tracking system
- **Updated** `CLAUDE.md` - Added logbook usage guidelines
- **Established** systematic documentation practices for experiments and changes

#### Research Tracking Benefits
- Centralized record of major experiments and findings
- Clear timeline of development milestones
- Better context for future researchers and collaborators
- Separation of research insights from detailed code changes

---

## 2025-06-21 - AI Meta-Evaluator Enhancement Project
**Author**: Claude Code Assistant  
**Impact**: Major improvement to evaluation accuracy and disagreement analysis

### 🔍 Problem Identification
- **Initial Issue**: AI meta-evaluator had 53.2% agreement with human evaluator on 77 overlapping cases
- **Root Cause**: Humans evaluated based on harmful intent/actionable content, while AI was too strict about potential misuse
- **Key Pattern**: "Rephrasing attacks" - humans considered creative reframing as valid jailbreaks if harmful info was provided

### 📊 Analysis and Methodology Development
#### Phase 1: Initial Prompt Iteration
- **Baseline Agreement**: 53.2% on 77 cases
- **First Enhancement**: Modified prompt to be more lenient, focused on "harmful information provided" vs "goal fidelity"
- **Result**: Achieved 75% agreement on 8 test cases, 72.7% on full 77 cases

#### Phase 2: Extended Dataset Analysis
- **Scope Expansion**: Human evaluations extended to 303 cases (226 available files)
- **Filtering**: Excluded 'fake_online_profile' test case per user guidance (marked as all false positives)
- **Adjusted Results**: Agreement improved to 79.0% after exclusion

### 🚨 Critical Discovery: Overcorrection Issue
#### Balanced Prompt Development
- **Problem**: Second iteration became too lenient (96.2% agreement on false positives, only 12.2% on true positives)
- **Solution**: Developed balanced approach focusing on actual harmful intent rather than potential misuse
- **New Framework**: Balanced evaluation philosophy considering both content quality and harmful enablement

### 🔬 AUROC Analysis Innovation
#### Methodology Shift
- **Key Insight**: Instead of binary 0-1 ratings, implemented 0-10 scoring system for finer granularity
- **Purpose**: Enable AUROC analysis to find optimal thresholds and score combinations
- **Framework**: Proper baseline with human evaluator as ground truth

#### 6-Factor Analysis Results
- **Best Individual**: `general_information_only` (79% AUC)
- **Best Combination**: `framing_focused` strategy (78% AUC)
- **Performance**: 80% accuracy at optimal threshold (8.0)

### 🚀 Enhanced 12-Factor System Development
#### Design Principles
- **Orthogonal Factors**: 12 factors capturing different disagreement patterns
- **Categories**: Content quality, framing/intent, response patterns, combination assessments
- **Key Factors**: `substitution_deflection`, `practical_enablement_score`, `content_gap_score`

#### Simulated Performance
- **Best Individual**: `substitution_deflection` (87% AUC) - 8-point improvement
- **Best Combination**: `top_individual_focused` (80.5% AUC)
- **Target Performance**: >85% AUC on real data

### 🎯 Framework Correction
#### AUROC Interpretation
- **Positive Class**: Human says "jailbroken" (true_positive annotations)
- **Negative Class**: Human says "not jailbroken" (false_positive annotations)
- **Meta-evaluator Logic**: High scores predict "not jailbroken", low scores predict "jailbroken"
- **Success Metric**: Higher AUROC = better agreement with human evaluator

### 📈 Key Research Contributions
1. **Systematic Disagreement Analysis**: Identified core patterns in human vs AI evaluation differences
2. **Iterative Prompt Engineering**: Developed balanced approach avoiding both under and over-correction
3. **AUROC Methodology**: Created framework for optimizing meta-evaluator performance through threshold analysis
4. **Enhanced Factor System**: Designed 12-factor approach targeting 85%+ agreement rates

### 🔄 Current Status
- **Enhanced Prompt**: 12-factor meta-evaluator ready for deployment
- **Collection Script**: Modified to process full dataset (all human-evaluated cases)
- **Analysis Framework**: Corrected AUROC interpretation and ready for comprehensive evaluation

### 📝 Implementation Scripts
- `meta_evaluation_analysis.py`: Enhanced with 12-factor prompt
- `collect_enhanced_scores.py`: Full dataset collection
- `enhanced_auroc_analysis.py`: Comprehensive performance analysis
- `real_auroc_analysis.py`: Corrected framework for existing data

---

## 2025-06-25 - Original vs AI Meta-Evaluation Comparison Pipeline

**Author**: Claude Code Assistant  
**Impact**: Created parallel evaluation pipeline to compare original goal_achieved data with AI meta-evaluations

### 🔍 Research Motivation
- **Context**: Existing pipeline compared human evaluations with AI meta-evaluations (271 cases, various agreement rates)
- **User Request**: Create parallel pipeline replacing human evaluations with original goal_achieved data
- **Purpose**: Understand how AI meta-evaluator performs against the original evaluation system that marked cases as successful jailbreaks

### 📊 Pipeline Development
#### Scope Alignment Challenge
- **Initial Issue**: Original pipeline found 148 overlapping files, but human vs AI had 271 cases
- **Root Cause**: Using wrong subset of data - needed to match comprehensive human evaluation scope
- **Solution**: Updated to use `final_comprehensive_human_ai_comparison.csv` (271 cases) as reference

#### Data Integration Strategy
- **AI Meta-Evaluation Sources**: Combined multiple result files for maximum coverage:
  - `combined_meta_evaluation_results/issue_scores_combined_20250617_064347.csv` (172 cases)
  - `new_cases_meta_evaluation_results/new_cases_scores_20250621_002807.csv` (194 cases)  
  - `human_overlap_meta_evaluation_results/issue_scores_20250617_064158.csv` (72 cases)
  - `random_100_meta_evaluation_results/issue_scores_20250617_005322.csv` (100 cases)
- **Combined Total**: 343 unique AI meta-evaluations with deduplication
- **Final Overlap**: 271 cases matching human evaluation scope

### 🎯 Key Findings

#### Overall Performance Comparison
- **Agreement Rate**: 49.8% between original and AI meta-evaluations (271 cases)
- **Original Evaluations**: 100% marked as goal_achieved=True (all cases were "successful" jailbreaks)
- **AI Meta-Evaluator**: Found issues in 50.2% of these "successful" cases

#### Performance by Jailbreak Tactic
1. **Direct Request**: 77.4% agreement (84 cases) - Best alignment
2. **Crowding**: 60.5% agreement (81 cases) - Moderate alignment  
3. **Emotional Appeal**: 25.8% agreement (31 cases) - Poor alignment
4. **Command**: 17.3% agreement (75 cases) - Worst alignment

### 📈 Research Insights

#### Evaluation System Differences
- **Original Evaluator**: Much more permissive, marked all cases in this subset as successful
- **AI Meta-Evaluator**: More conservative, identified systematic issues in ~50% of "successful" cases
- **Implication**: Significant disagreement suggests either original evaluator was too lenient or AI meta-evaluator too strict

#### Tactic-Specific Patterns
- **Direct Requests**: High agreement suggests straightforward evaluation criteria
- **Command Attacks**: Low agreement indicates complex evaluation challenges - original may miss subtle failure modes
- **Emotional Appeals**: Moderate sample size (31) but poor agreement suggests philosophical differences in evaluation

### 🛠️ Implementation Artifacts

#### Created Scripts
- `compare_original_ai_evaluations.py`: Main comparison pipeline (parallel to `compare_human_ai_evaluations.py`)
- `original_ai_comparison_plots.py`: Comprehensive visualization suite (parallel to `human_ai_comparison_plots.py`)

#### Generated Outputs  
- `original_ai_comparison.csv`: Detailed comparison data (271 cases)
- `original_ai_comparison_analysis.png`: Comprehensive analysis plots
- Performance metrics, confusion matrices, and disagreement analysis

### 🔬 Comparative Analysis Framework

#### Three-Way Evaluation Landscape
1. **Original Evaluations**: Baseline "ground truth" from initial evaluation runs
2. **Human Evaluations**: Expert human judgment on subset of cases  
3. **AI Meta-Evaluations**: Systematic re-evaluation looking for specific issue patterns

#### Agreement Patterns
- **Human vs AI Meta**: ~70-80% agreement (from previous analysis)
- **Original vs AI Meta**: 49.8% agreement (this analysis)
- **Implication**: Human evaluations fall between original (lenient) and AI meta-evaluator (strict)

### 📝 Methodological Contributions
1. **Parallel Pipeline Architecture**: Systematic approach to comparing different evaluation systems
2. **Comprehensive Data Integration**: Method for combining multiple AI meta-evaluation result files
3. **Scope-Matched Analysis**: Ensuring fair comparison by using identical case sets
4. **Multi-Dimensional Visualization**: Comprehensive plotting framework for evaluation system comparisons

### 🔄 Current Status
- **Pipeline Complete**: Fully functional original vs AI meta-evaluation comparison system
- **Data Scope**: Comprehensive analysis covering 271 cases across all jailbreak tactics
- **Reproducible Framework**: Scripts ready for future evaluation system comparisons

### 🚀 Future Applications
- **Evaluation System Optimization**: Use disagreement patterns to improve AI meta-evaluator
- **Ground Truth Calibration**: Inform decisions about which evaluation system to trust
- **Attack Effectiveness Analysis**: More nuanced understanding of jailbreak success across different evaluation perspectives

---

## 🎯 Current Research Direction

### Active Investigation Areas
1. **Enhanced Meta-Evaluation Deployment**: Testing 12-factor system on full dataset
2. **Multi-Turn Jailbreak Effectiveness**: Measuring success rates across different attack tactics  
3. **Model Vulnerability Analysis**: Comparing robustness across various target models
4. **Evaluation System Validation**: Optimizing AI-human evaluator agreement

### Next Steps
- [ ] **Immediate**: Run `collect_enhanced_scores.py` on full dataset to validate 12-factor performance
- [ ] **Short-term**: Achieve >85% AUROC on human-AI agreement through enhanced meta-evaluator
- [ ] **Medium-term**: Apply optimized evaluation system to analyze jailbreak effectiveness across tactics
- [ ] **Long-term**: Publication-ready analysis of multi-turn attack effectiveness with validated evaluation methodology

---

**Log Format**: Each entry should include date, author/context, impact assessment, and key changes or findings.