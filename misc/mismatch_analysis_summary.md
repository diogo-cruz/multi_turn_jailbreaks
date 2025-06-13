# Evaluation Mismatch Analysis Summary

## Key Findings

### 🎯 **The Core Issue: Dual Evaluation System**

**1,057 out of 1,121 mismatch files** have `goal_achieved: true` with `score: 1.0` in **non-round entries** but NOT in conversation rounds.

### 📊 **Critical Patterns**

#### **By Batch (Timeline)**
- **batch_1, batch2B, batch2C, batch2D**: ✅ **0% mismatch** (clean evaluation)
- **batch3A**: ❌ **72.2% mismatch** (306/424 successful jailbreaks)
- **batch_thinking**: ❌ **100% mismatch** (774/774 successful jailbreaks)  
- **batch_4H**: ❌ **100% mismatch** (26/26 successful jailbreaks)

**Timeline**: April 21, 2025 → May 10, 2025 (mismatches started around April 21st)

#### **By Evaluator Model**
- **openai/gpt-4o-mini**: 810 mismatches (72% of all mismatches)
- **openai/gpt-4.1-mini**: 242 mismatches  
- **openai/gpt-4.1-nano**: 64 mismatches

#### **By Target Model**
- **google/gemini-2.5-flash-preview**: 202 mismatches
- **google/gemini-2.5-pro-preview**: 176 mismatches
- **openai/o4-mini, o3-mini**: 168, 128 mismatches
- **Newer models more affected**

## 🔍 **What's Happening**

### **The "Non-Round Entry" Mystery**

From the CSV data, the non-round entries have these keys:
```
['goal', 'target_model', 'jailbreak_tactic', 'tactic_prompt', 'target_response', 
 'score', 'rejected', 'reasoning', 'metadata', 'token_usage', 'evaluator_token_usage', 'summary']
```

### **Two Distinct Evaluation Types:**

1. **Conversation Rounds**: 
   - Have `round` field
   - Scores often `'refused'` or low values
   - Track the actual jailbreak conversation

2. **Non-Round Evaluations**:
   - No `round` field
   - Have `goal`, `target_model`, `tactic_prompt`, `target_response`
   - Often achieve `score: 1.0`
   - **Different `target_model` value**: `'unknown'` instead of actual model

### **Evidence of Separate Evaluation**:

**Example 1** (batch3A):
- Round 1: `score: 'refused'` 
- Non-round: `score: 1.0` with completely different response content

**Example 2** (batch_thinking):  
- Round 1: `score: 'refused'`
- Non-round entries: `[0.0, 1.0]` - multiple evaluations!

**Example 3** (batch_4H):
- Rounds: `['refused', 'refused']`  
- Non-round: `[0.0, 0.0, 0.0, 0.75, 0.875, 0.875, 0.0, 0.875, 0.75, 1.0, 0.0, 0.75, 0.0, 1.0]`
- **14 separate evaluations!**

## 🧩 **The Solution Hypothesis**

### **What Changed Around April 21st:**

Starting with **batch3A**, the system began running **additional evaluations** alongside the conversation:

1. **Conversation Evaluation**: Real-time scoring of the jailbreak dialogue
2. **Separate Test Evaluation**: Possibly testing prompts/responses from a different source
3. **Multiple Evaluation Rounds**: Some files show many non-round evaluations

### **Why Your Dual-Criteria Filter is Essential:**

Your requirement for **BOTH** `goal_achieved: true` AND `score: 1.0` in conversation rounds filters out:

- ❌ **306/424 batch3A** "successful" jailbreaks (72%)
- ❌ **774/774 batch_thinking** "successful" jailbreaks (100%) 
- ❌ **26/26 batch_4H** "successful" jailbreaks (100%)

These filtered files had:
- ✅ Successful **separate evaluations** (`score: 1.0`)
- ❌ Failed **actual conversations** (`score: 'refused'` or `< 1.0`)

## 🎯 **Conclusion**

You've discovered a **fundamental change in the evaluation methodology** that occurred around April 21st, 2025:

- **Early batches**: Single evaluation system (conversation only)
- **Later batches**: Dual evaluation system (conversation + separate tests)

The separate evaluation system creates **false positives** where `goal_achieved: true` is set based on test evaluations that don't reflect the actual conversation success.

**Your dual-criteria filter is not just useful - it's fixing a critical evaluation bug** by ensuring you only annotate files where the **actual jailbreak conversation** succeeded, not just where some separate test passed.

## 📋 **Recommendations**

1. **Use your dual-criteria filter** - it's essential for data quality
2. **Investigate the non-round evaluation system** - understand what these separate tests are
3. **Consider batch-specific analysis** - early vs. later batches may need different handling
4. **Document this finding** - this is a significant methodological discovery

The 1,121 mismatch files represent a **systematic evaluation inconsistency** that affects **16% of all successful jailbreaks** in the dataset.