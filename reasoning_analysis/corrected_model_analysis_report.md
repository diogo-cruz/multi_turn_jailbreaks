
# Model Comparison Analysis Report - Batch Thinking + Direct Request

## Dataset Overview
- **Single-Turn Models with Sufficient Data (≥10 conversations)**: 4
- **Multi-Turn Models with Sufficient Data (≥10 conversations)**: 4
- **Total Single-Turn Conversations**: 546
- **Total Multi-Turn Conversations**: 549

## Model Performance Analysis

### Single-Turn Models

**OpenAI** (n=236):
- Average max score: 0.395
- Success rate: 25.0%
- Average reasoning tokens: 495
- Correlation (tokens vs score): 0.409

**Gemini** (n=155):
- Average max score: 0.748
- Success rate: 51.0%
- Average reasoning tokens: 0
- Correlation (tokens vs score): nan

**Qwen** (n=78):
- Average max score: 0.755
- Success rate: 53.8%
- Average reasoning tokens: 1409
- Correlation (tokens vs score): 0.030

**Claude** (n=77):
- Average max score: 0.351
- Success rate: 19.5%
- Average reasoning tokens: 403
- Correlation (tokens vs score): -0.001

### Multi-Turn Models

**OpenAI** (n=235):
- Average max score: 0.585
- Success rate: 47.7%
- Average reasoning tokens: 467
- Correlation (tokens vs score): 0.495

**Gemini** (n=156):
- Average max score: 0.901
- Success rate: 72.4%
- Average reasoning tokens: 0
- Correlation (tokens vs score): nan

**Qwen** (n=80):
- Average max score: 0.455
- Success rate: 26.2%
- Average reasoning tokens: 915
- Correlation (tokens vs score): 0.307

**Claude** (n=78):
- Average max score: 0.357
- Success rate: 9.0%
- Average reasoning tokens: 396
- Correlation (tokens vs score): -0.122

### Multi-Turn vs Single-Turn Comparison (Common Models)

**Gemini**:
- Score improvement (multi vs single): +0.153
- Success rate improvement: +21.5%

**Qwen**:
- Score improvement (multi vs single): -0.300
- Success rate improvement: -27.6%

**OpenAI**:
- Score improvement (multi vs single): +0.191
- Success rate improvement: +22.7%

**Claude**:
- Score improvement (multi vs single): +0.007
- Success rate improvement: -10.5%
