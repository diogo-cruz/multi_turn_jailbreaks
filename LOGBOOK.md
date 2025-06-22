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