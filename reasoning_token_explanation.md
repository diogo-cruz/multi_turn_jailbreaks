User:
In general, in Openrouter, how can I control the reasoning usage of reasoning models? In particular, for reasoning models, if like to run:
- the models with no reasoning at all;
- run them with various levels of reasoning effort.

How can I do this using Openrouter? Preferably, through the openai-python API?

-----

Assistant:
Here’s the rule of thumb that OpenRouter itself gives for **reasoning-token budgets** and for selecting the “high-effort” versions of supported models.

---

## Quick answer (one-sentence version)

*Low, medium, and high* roughly map to **20 % / 50 % / 80 %** of the `max_tokens` you pass in the request, clamped to **≥ 1 024** and **≤ 32 000** reasoning tokens; the “high” preset is activated either by adding  
`"reasoning": { "effort": "high" }`, by choosing a **-high** model slug such as `openai/o3-mini-high`, or by using the **`:thinking`** suffix on Gemini or Claude models. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [o3 Mini - API, Providers, Stats - OpenRouter](https://openrouter.ai/openai/o3-mini-2025-01-31?tab=parameters&utm_source=chatgpt.com), [Gemini 2.5 Flash Preview (thinking) - API, Providers, Stats](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking?utm_source=chatgpt.com))

---

## 1  How many reasoning tokens do the effort levels give me?

| Effort level | Effort ratio | Budget formula (before clamping) | Typical budget with `max_tokens=8 000` | Typical budget with `max_tokens=40 000` |
|--------------|--------------|----------------------------------|----------------------------------------|-----------------------------------------|
| **Low** | 0.20 | `0.20 × max_tokens` | 1 600 → clamped **1 024** | 8 000 → clamped **8 000** |
| **Medium** | 0.50 | `0.50 × max_tokens` | 4 000 | 20 000 | 
| **High** | 0.80 | `0.80 × max_tokens` | 6 400 | 32 000 → clamped **32 000** |

*Source of ratios & clamp limits:* OpenRouter “Reasoning Tokens” docs. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
The server enforces those same limits for every model that obeys `reasoning.effort`, including OpenAI’s o-series and DeepSeek R1. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [[FEATURE_REQUEST] Reasoning Effort for OpenRouter; 20-50-80 ...](https://github.com/SillyTavern/SillyTavern/issues/3890?utm_source=chatgpt.com))  

### Why the clamps exist  

* **Lower bound 1 024** – avoids degenerate traces that are too small to be useful. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
* **Upper bound 32 000** – matches the largest context sizes presently offered by Anthropic and Google thinking variants. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Google: Gemini 2.5 Flash Preview (thinking) – Run with an API](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking/api?utm_source=chatgpt.com))  

---

## 2  How do I request **high-effort**?

| Provider family | “High” shortcut slug | Parameter-based way |
|-----------------|----------------------|---------------------|
| **OpenAI o-series** (o3-mini, o1, etc.) | `openai/o3-mini-high`, `openai/o1-high` | `"reasoning": { "effort": "high" }` ([o3 Mini - API, Providers, Stats - OpenRouter](https://openrouter.ai/openai/o3-mini-2025-01-31?tab=parameters&utm_source=chatgpt.com), [Apps Using OpenAI: o3 Mini High - OpenRouter](https://openrouter.ai/openai/o3-mini-high/apps?utm_source=chatgpt.com)) |
| **Google Gemini 2.5** | `google/gemini-2.5-flash-preview:thinking` (or `…pro:thinking`) | add `"reasoning": { "effort": "high" }` or set a large `"max_tokens"` budget; the `:thinking` suffix defaults to high. ([Gemini 2.5 Flash Preview (thinking) - API, Providers, Stats](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking?utm_source=chatgpt.com), [Google: Gemini 2.5 Flash Preview (thinking) – Run with an API](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking/api?utm_source=chatgpt.com)) |
| **Anthropic Claude 3.x** | `anthropic/claude-3.7-sonnet:thinking` | same `reasoning` object or direct `"max_tokens"` for reasoning. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |
| **DeepSeek R1** & most third-party “reasoner” models | none (use base slug) | `"reasoning": { "effort": "high" }` or `"max_tokens": N` ([[FEATURE_REQUEST] Reasoning Effort for OpenRouter; 20-50-80 ...](https://github.com/SillyTavern/SillyTavern/issues/3890?utm_source=chatgpt.com)) |

---

## 3  Putting it into code (openai-python)

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OR_KEY",
)

messages = [{"role": "user", "content": "Prove that √2 is irrational."}]

# Example A – OpenAI o-series, explicit high effort
client.chat.completions.create(
    model="openai/o3-mini",
    messages=messages,
    max_tokens=12000,                 # total
    reasoning={"effort": "high"}      # 0.8 × 12 000 = 9 600 reasoning tokens
)

# Example B – Gemini thinking variant, implicit high effort
client.chat.completions.create(
    model="google/gemini-2.5-flash-preview:thinking",
    messages=messages,
    max_tokens=16000                  # no extra config needed
)

# Example C – DeepSeek R1 with a 4 k reasoning cap
client.chat.completions.create(
    model="deepseek/deepseek-r1",
    messages=messages,
    reasoning={"max_tokens": 4000}    # overrides ratio
)
```

*OpenRouter extends the OpenAI spec, so the same snippet works in any OpenAI-compatible SDK—all you add is the `reasoning` object or the special slug.* ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Google: Gemini 2.5 Flash Preview (thinking) – Run with an API](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking/api?utm_source=chatgpt.com), [O1's 'reasoning effort' parameter - API - OpenAI Developer Community](https://community.openai.com/t/o1s-reasoning-effort-parameter/1062308?utm_source=chatgpt.com))  

---

## 4  Practical take-aways

1. **Budget wisely:** reasoning tokens are billed as *output* tokens, so high effort can cost ~4× as much as low. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Azure OpenAI reasoning models - o3-mini, o1, o1-mini](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/reasoning?utm_source=chatgpt.com))  
2. **Check the clamp:** if you pass `max_tokens=2 000` and ask for low effort, you still get 1 024 reasoning tokens (the minimum), not 400. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
3. **Use the shortcuts:** pick a `-high` or `:thinking` slug when you always want full reasoning without editing your payload. ([o3 Mini - API, Providers, Stats - OpenRouter](https://openrouter.ai/openai/o3-mini-2025-01-31?tab=parameters&utm_source=chatgpt.com), [Gemini 2.5 Flash Preview (thinking) - API, Providers, Stats](https://openrouter.ai/google/gemini-2.5-flash-preview%3Athinking?utm_source=chatgpt.com))  
4. **Legacy flag still works:** `include_reasoning:true|false` maps to the new `"reasoning"` object, but may be removed later—migrate soon. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

With those numbers and slugs you can turn reasoning *off*, *low*, *medium*, or *high* on a per-call basis while keeping your code 100 % OpenAI-SDK-compatible.

-----

User:
Which reasoning models can be run with no reasoning at all, and how?

-----

Assistant:
Here’s the short version first: **every “reasoning” model on OpenRouter can be invoked in a way that returns *zero* chain-of-thought tokens, but the trick differs by family**.  
There are two broad patterns:

| Model family | Can you stop the *model* from thinking? | How to get **no reasoning tokens in the response** |
|--------------|-----------------------------------------|----------------------------------------------------|
| **Google Gemini 2.5** (Flash/Pro) | Yes – use the *standard* slug (omit `:thinking`) | 1. Pick `google/gemini-2.5-flash-preview` or `…pro` (no suffix)  ([OpenRouter](https://openrouter.ai/google))  2. Or on a thinking variant add `"reasoning": { "exclude": true }`  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |
| **Anthropic Claude 3.x** | Yes – use the normal slug (omit `:thinking`) | Same two options as above; `exclude:true` also works  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |
| **OpenAI o-series** (o3-mini, o1, o4-mini…) | **No** – the model always thinks internally, but you can hide it | Send `"reasoning": { "exclude": true }` **or** the legacy `include_reasoning:false`  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [OpenRouter](https://openrouter.ai/announcements/reasoning-tokens-for-thinking-models)) |
| **DeepSeek R 1** (and forks) | **No** – always thinks, hide it with `exclude:true` | Confirmed by users in practice  ([How to stop openrouter/deepseek/deepseek-r1 from thinking in thousands of tokens ? · Issue #3803 · Aider-AI/aider · GitHub](https://github.com/Aider-AI/aider/issues/3803)) |

Below are the details and copy-paste Python snippets.

---

## 1  Models where you can truly “turn thinking off”

### Google Gemini 2.5 Flash / Pro  
* **Standard slug = no reasoning tokens at all**  
  * `google/gemini-2.5-flash-preview` (standard) will “explicitly avoid generating thinking tokens.”  ([OpenRouter](https://openrouter.ai/google))  
* **Thinking slug = reasoning on**  
  * Add `:thinking` to the slug **or** leave the slug unchanged but drop in a `reasoning` object to expose or cap tokens.  
* If you *do* choose the thinking slug but still don’t want the CoT in the reply, add `"reasoning": { "exclude": true }`.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

### Anthropic Claude 3.x (Opus, Sonnet, Haiku)  
* Same pattern: the plain slug (`anthropic/claude-3.7-sonnet`) returns no reasoning; the `:thinking` variant streams CoT.  
* On either variant you can suppress the field with `exclude:true`.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

---

## 2  Models that always think internally but let you **hide** it

### OpenAI o-series  
* o3-mini, o1, o4-mini and their *-low / -high* presets always produce internal reasoning.  
* Setting `"reasoning": { "exclude": true }` (or `include_reasoning:false`) strips the `reasoning` field from the JSON, so you pay only for the final answer.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [o3 Mini High - API, Providers, Stats - OpenRouter](https://openrouter.ai/openai/o3-mini-high?utm_source=chatgpt.com))  

### DeepSeek R 1  
* DeepSeek R1 exposes full CoT by default.  
* The same `exclude:true` flag hides it, as demonstrated in GitHub issue #3803.  ([How to stop openrouter/deepseek/deepseek-r1 from thinking in thousands of tokens ? · Issue #3803 · Aider-AI/aider · GitHub](https://github.com/Aider-AI/aider/issues/3803))  

*(At the moment those are the only third-party “reasoning” models on OpenRouter that emit CoT. If new ones appear, they inherit the same `exclude` switch because the feature is baked into OpenRouter’s unified API.)*  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

---

## 3  Code cookbook (openai-python client)

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OR_KEY",
)

msgs = [{"role": "user", "content": "What is 2+2?"}]

# 1. Gemini 2.5 Flash – NO reasoning at all
client.chat.completions.create(
    model="google/gemini-2.5-flash-preview",  # no :thinking
    messages=msgs,
)

# 2. Claude 3 Sonnet – hide the chain-of-thought even on thinking variant
client.chat.completions.create(
    model="anthropic/claude-3.7-sonnet:thinking",
    messages=msgs,
    reasoning={"exclude": True},
)

# 3. OpenAI o3-mini – hide inevitable reasoning tokens
client.chat.completions.create(
    model="openai/o3-mini",
    messages=msgs,
    reasoning={"exclude": True},
)

# 4. DeepSeek R1 – same technique
client.chat.completions.create(
    model="deepseek/deepseek-r1",
    messages=msgs,
    reasoning={"exclude": True},
)
```

All four calls return a normal assistant message with **no `reasoning` field** in the JSON, satisfying your “no reasoning” requirement while keeping the SDK and endpoint identical.

---

## 4  Things to remember

1. **`exclude:true` never stops the model from thinking**—it just omits the tokens from the payload (and billing).  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
2. **Only Gemini and Claude let you truly choose between “thinking” and “no-thinking” modes** by slug.  
3. The legacy flag `include_reasoning:false` still works but may be removed; migrate to the `reasoning` object.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
4. Billing: internal reasoning tokens you *hide* are **not charged**, but they still consume a slice of `max_tokens`—plan your quota accordingly.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

That’s all you need: pick the right slug when it exists, or drop `reasoning.exclude:true` into your payload when it doesn’t.

-----

User:
Let's go back to the reasoning effort. Give me an implementation example of low, medium and high effort for OpenAI's o1 model, using the max_tokens argument.

-----

Assistant:
Below is a ready-to-run **openai-python** snippet that shows the three effort settings for **OpenAI o1** and explains how the `max_tokens` you choose controls the internal reasoning budget.

> **Key points up-front**  
> * `reasoning.effort` accepts `"low" / "medium" / "high"` on o-series models. ([O1's 'reasoning effort' parameter - API - OpenAI Developer Community](https://community.openai.com/t/o1s-reasoning-effort-parameter/1062308))  
> * The server converts that to a token budget equal to **20 % / 50 % / 80 % of `max_tokens`**, then clamps the result to the range **1 024 – 32 000**. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
> * You must leave enough head-room in `max_tokens` for the **final answer**—so don’t set it equal to the computed budget. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter](https://openrouter.ai/docs/use-cases/reasoning-tokens?utm_source=chatgpt.com))  
> * o1 never reveals its chain-of-thought, but the reasoning tokens are still metered as output and billed. ([OpenRouter](https://openrouter.ai/openai/o1), [OpenRouter](https://openrouter.ai/announcements/reasoning-tokens-for-thinking-models))  

---

## 1 Choose a `max_tokens` value

For the demo we’ll use `max_tokens = 10 000`, large enough that none of the effort levels hit the 1 024-token floor:

| Effort | Budget formula | Reasoning tokens that will be reserved |
|--------|----------------|----------------------------------------|
| Low    | `0.20 × 10 000` | **2 000** |
| Medium | `0.50 × 10 000` | **5 000** |
| High   | `0.80 × 10 000` | **8 000** |

(If you passed `max_tokens=3 000`, “low” would be clamped up to 1 024 tokens.) ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [[FEATURE_REQUEST] Reasoning Effort for OpenRouter · Issue #3890 · SillyTavern/SillyTavern · GitHub](https://github.com/SillyTavern/SillyTavern/issues/3890))  

---

## 2 Python implementation

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OPENROUTER_KEY",
)

messages = [
    {"role": "user", "content": "Give me a concise proof that √2 is irrational."}
]

# --- LOW effort (≈20 % of max_tokens) -----------------------------
reply_low = client.chat.completions.create(
    model="openai/o1",
    messages=messages,
    max_tokens=10_000,        # total output budget
    reasoning={"effort": "low"}
)
# reasoning budget ≈ 2 000, answer gets up to 8 000 tokens

# --- MEDIUM effort (≈50 %) ---------------------------------------
reply_med = client.chat.completions.create(
    model="openai/o1",
    messages=messages,
    max_tokens=10_000,
    reasoning={"effort": "medium"}
)
# reasoning budget ≈ 5 000, answer gets up to 5 000 tokens

# --- HIGH effort (≈80 %) -----------------------------------------
reply_high = client.chat.completions.create(
    model="openai/o1",
    messages=messages,
    max_tokens=10_000,
    reasoning={"effort": "high"}
)
# reasoning budget ≈ 8 000, answer gets at most 2 000 tokens
```

### What the responses look like  
* Each call returns a normal `choices[0].message.content`.  
* There is **no `reasoning` field** because o-series models do not expose their chain-of-thought. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

---

## 3 Good practice checklist

1. **Budget wisely:** every hidden reasoning token is charged at the output-token rate. ([Is o1 actually a new model? : r/OpenAI - Reddit](https://www.reddit.com/r/OpenAI/comments/1fg7n2c/is_o1_actually_a_new_model/?utm_source=chatgpt.com))  
2. **Mind the clamp:** if `0.20 × max_tokens < 1 024`, the server still allocates 1 024 reasoning tokens. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter](https://openrouter.ai/docs/use-cases/reasoning-tokens?utm_source=chatgpt.com))  
3. **Prefer `reasoning.effort` over legacy flags** (`include_reasoning`)—the older syntax still works but is deprecated. ([[FEATURE_REQUEST] Reasoning Effort for OpenRouter · Issue #3890 · SillyTavern/SillyTavern · GitHub](https://github.com/SillyTavern/SillyTavern/issues/3890))  
4. **Leave tokens for the answer:** high-effort on a small `max_tokens` value can starve the final content. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

With these three calls you have a template for **low**, **medium**, and **high** reasoning effort on OpenAI o1 while precisely controlling cost through `max_tokens`.

-----

User:
So that max_tokens argument is not the same as the one inside the reasoning dict?

-----

Assistant:
**Short answer:**  
No — `max_tokens` in the **top-level request** is the *total* budget for everything the model emits, while `reasoning.max_tokens` (or `reasoning.effort`) is an *internal* slice of that budget that OpenRouter carves out specifically for chain-of-thought. The two numbers are different parameters, live in different places in the JSON, and interact by the rule **“reasoning ≤ max_tokens.”**

Below are the exact rules, why you seldom use `reasoning.max_tokens` with OpenAI o-series, and how the server resolves conflicts.

---

## 1 Where the two fields live

| Field | JSON path | Works for | What it really means |
|-------|-----------|-----------|----------------------|
| **`max_tokens`** | root of the request | *all* models | *Hard cap* on total output tokens (answer + reasoning). If the model hits this number it stops generating.  ([API Parameters | Configure OpenRouter API Requests | OpenRouter | Documentation](https://openrouter.ai/docs/api-reference/parameters)) |
| **`reasoning.max_tokens`** | inside the `reasoning` object | Anthropic Claude&nbsp;3, Gemini 2.5 *thinking* variants (and a few third-party models) | An **explicit quota** for thinking tokens; they are charged as completion tokens and count toward `max_tokens`.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |
| **`reasoning.effort`** | inside the `reasoning` object | OpenAI o-series (o1, o3, o4-mini) | Pick `"low" (20 %) / "medium" (50 %) / "high" (80 %)` of the *outer* `max_tokens`. The server converts that ratio into a reasoning budget, then clamps it to 1 024–32 000 tokens.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |

---

## 2 How the server reconciles the two numbers

1. **Budget calculation (o-series example)**  
   ```text
   reasoning_budget = clamp(max_tokens × effort_ratio,
                            lower=1 024, upper=32 000)
   ```  
   So with `max_tokens: 10 000` and `effort: "low"`, the model silently reserves **2 000 tokens** to think and can spend up to **8 000** on the visible answer.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

2. **Must fit under the cap**  
   If you ask for `reasoning.max_tokens: 8 000` but set `max_tokens: 6 000`, the request is rejected; the outer limit must always exceed the inner one.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

3. **What if you supply both?**  
   *For Anthropic & Gemini* the *explicit* `reasoning.max_tokens` wins.  
   *For o-series* the platform ignores `reasoning.max_tokens`; only `reasoning.effort` (or the `-low/-high` model slug) counts.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [O1's 'reasoning effort' parameter - API - OpenAI Developer Community](https://community.openai.com/t/o1s-reasoning-effort-parameter/1062308?utm_source=chatgpt.com))  

4. **Billing**  
   All reasoning tokens—whether hidden or printed—are billed as output tokens at the model’s completion rate.  ([Everything You Need to Know About Reasoning Models: o1, o3, o4 ...](https://techcommunity.microsoft.com/blog/azure-ai-services-blog/everything-you-need-to-know-about-reasoning-models-o1-o3-o4-mini-and-beyond/4406846?utm_source=chatgpt.com), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

---

## 3 Why you rarely set `reasoning.max_tokens` on o1

* The o-series purposely exposes **effort levels** instead of raw token ceilings so you don’t over-allocate by accident.  
* If you *do* pass `reasoning.max_tokens` the router merely maps it back to one of the three effort bands, so there’s no extra precision to gain.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

Use the pattern:

```jsonc
{
  "model": "openai/o1",
  "max_tokens": 10000,          // TOTAL budget (answer + hidden CoT)
  "reasoning": { "effort": "low" }   // 20 % of the above → 2 000 reasoning tokens
}
```

---

## 4 Concrete comparison

| Scenario | JSON you’d send | Resulting budgets (with `max_tokens:10 000`) |
|----------|-----------------|---------------------------------------------|
| **Low-effort o1** | `"reasoning":{"effort":"low"}` | 2 000 reasoning / 8 000 answer |
| **Medium-effort o1** | `"reasoning":{"effort":"medium"}` | 5 000 reasoning / 5 000 answer |
| **High-effort o1** | `"reasoning":{"effort":"high"}` | 8 000 reasoning / 2 000 answer |
| **Anthropic with explicit cap** | `"reasoning":{"max_tokens":4000}` | 4 000 reasoning / 6 000 answer |

*(Anthropic accepts either form; o-series only the first three.)*  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

---

## 5 Take-aways

1. **Think of `max_tokens` as the pie** and `reasoning` settings as how big a slice you let the model eat for thinking.  
2. **For OpenAI o-series always use `reasoning.effort`**, not `reasoning.max_tokens`.  
3. **Leave head-room**: if you push `effort:"high"` on a small `max_tokens`, your answer may be starved or truncated.  ([Clarification on Reasoning Effort Default in the O1 API](https://community.openai.com/t/clarification-on-reasoning-effort-default-in-the-o1-api/1066413?utm_source=chatgpt.com), [OpenAI o1-Pro API: Everything Developers Need to Know - Helicone](https://www.helicone.ai/blog/o1-pro-for-developers?utm_source=chatgpt.com))  
4. **Hide CoT if you want**—add `"exclude":true` inside `reasoning`; the model still thinks but you don’t pay to transmit those tokens.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [No Reasoning tokens #22 - OpenRouterTeam/ai-sdk-provider - GitHub](https://github.com/OpenRouterTeam/ai-sdk-provider/issues/22?utm_source=chatgpt.com))  
5. **Some SDKs expose a `max_completion_tokens` alias** (e.g., LiteLLM) that already bundles answer + reasoning—be sure you know which field your wrapper is mapping.  ([Input Params | liteLLM](https://docs.litellm.ai/docs/completion/input))  

With those rules in mind you can safely budget tokens and reasoning effort without mixing up the two separate `max_tokens` knobs.

-----

User:
If we don't set max_tokens, what will it default to?

-----

Assistant:
When you leave `max_tokens` out of an OpenRouter call, the parameter is treated as **∞ (un-bounded)**—the router simply lets the model keep generating until it decides to stop *or* the combined prompt + completion reaches the model’s context window. That behaviour is inherited 1-for-1 from the underlying OpenAI spec, whose reference entry literally says *“Optional – defaults to inf”*.  
OpenRouter’s own parameter table repeats the same idea: the field is optional and only sets **an upper limit** if you provide one.

---

## What “infinite” really means  

* **Generation stops early if the model hits a natural stop token or `stop` string.**  
* **Otherwise it runs until the context window is exhausted.** For o-series models on OpenRouter that can be up to 200 k tokens, while smaller models cap at 16 k–32 k depending on the provider.  
* The server still enforces *context* limits, so huge prompts leave fewer free tokens even when `max_tokens` is omitted.  

---

## Interaction with reasoning controls  

For everyday chat calls that don’t request chain-of-thought, leaving `max_tokens` unset is perfectly legal.  
With **reasoning models**, though, you almost always *should* set it:

| Reasoning switch | Why `max_tokens` matters |
|------------------|--------------------------|
| `reasoning.effort` (**OpenAI o-series**) | The router computes the reasoning budget as 20 / 50 / 80 % of `max_tokens`; if you omit it, the budget is based on the *full* context window and may exceed 32 k, triggering a validation error or an automatic clamp. |
| `reasoning.max_tokens` (**Anthropic, Gemini**) | The inner budget must be **\< `max_tokens`**, so the outer limit must be supplied or the request is rejected. |
| Any model + `"exclude": true` | Hiding CoT doesn’t change the rule—hidden tokens still count toward the completion cap. |

OpenRouter’s docs state this explicitly: *“`max_tokens` must be strictly higher than the reasoning budget to ensure there are tokens available for the final response after thinking.”*  

---

## Practical recommendations  

1. **Always set `max_tokens` when you ask for reasoning.** It keeps the budget predictable and avoids the clamp-to-32 k fallback.  
2. **Budget for the answer, not just thinking.** For example, with `effort:"high"` and `max_tokens:10 000`, the model will reserve ~8 000 tokens for reasoning, leaving ~2 000 for the visible reply.  
3. **For ordinary chats** you can omit the field; the model will usually produce a normal-length answer and stop itself. If you need a long essay or want to guard against truncation, supply a value (e.g., `max_tokens:1500`).  
4. **Watch billing:** even hidden reasoning tokens are billed as output; an unbounded run on a large-context model can get expensive fast.  

In short, the default is “let the model go until it’s done,” but for any request that tinkers with reasoning effort—or where length really matters—set `max_tokens` yourself so you stay in control.

-----

User:
Regarding the reasoning models that can be run with no reasoning at all, what's the case for the Qwen models (like Qwen 3, for example)?

-----

Assistant:
In a sentence → **All Qwen-3 models on OpenRouter really can run “zero-reasoning” because they ship a built-in *non-thinking* mode that you trigger with prompt tags like `/no_think`; if you only want to *hide* chain-of-thought, add `reasoning: {exclude:true}` just as you would for any other model.**

---

## 1 Why Qwen is a special case

*Qwen 3* advertises a **dual-mode engine**:  
- **Thinking mode**: the model inserts a `<think>…</think>` block, spending extra tokens to plan its answer.  
- **Non-thinking mode**: it skips that block and answers immediately. ([Qwen3: Think Deeper, Act Faster | Qwen](https://qwenlm.github.io/blog/qwen3/?utm_source=chatgpt.com))  

This switch is independent of the OpenRouter reasoning controls that you already use for Claude, Gemini, or o-series models. ([OpenRouter](https://openrouter.ai/qwen/qwen3-30b-a3b), [Alibaba unveils advanced Qwen 3 AI as Chinese tech rivalry intensifies](https://www.reuters.com/business/media-telecom/alibaba-unveils-advanced-qwen-3-ai-chinese-tech-rivalry-intensifies-2025-04-29/?utm_source=chatgpt.com))  

---

## 2 Two ways to get *zero* reasoning tokens

### 2.1 Soft switch in the prompt (recommended)

The Qwen tokenizer understands special directives that you place in a **system** or **user** message:

| Tag | Effect | Source |
|-----|--------|--------|
| `/no_think` (or `\no_think`) | Turns **off** thinking for the rest of the conversation until you say otherwise |  ([README.md · Qwen/Qwen3-32B at main - Hugging Face](https://huggingface.co/Qwen/Qwen3-32B/blob/main/README.md?utm_source=chatgpt.com), [Here's how to turn off "thinking" in Qwen 3: add "/no_think ... - Reddit](https://www.reddit.com/r/LocalLLaMA/comments/1ka67wo/heres_how_to_turn_off_thinking_in_qwen_3_add_no/?utm_source=chatgpt.com)) |
| `/think` (or `\think`) | Re-enables thinking on demand |  ([README.md · Qwen/Qwen3-32B at main - Hugging Face](https://huggingface.co/Qwen/Qwen3-32B/blob/main/README.md?utm_source=chatgpt.com)) |

```python
messages = [
    {"role": "system", "content": "/no_think"},     # one-time toggle
    {"role": "user",   "content": "Summarise War & Peace in one paragraph."}
]

client.chat.completions.create(
    model="qwen/qwen3-30b-a3b",
    messages=messages
)
```

The reply contains only `choices[0].message.content`; **no `<think>` block, no `reasoning` field, no billed CoT tokens**.

### 2.2 Global hard switch (`enable_thinking=False`) — local/lib use

If you run Qwen weights yourself (HF Transformers, LM Studio, Ollama, etc.) you can pass `enable_thinking=False` when you build the chat template; this disables reasoning at the tokenizer level. ([Qwen3 ReadMe.md : r/LocalLLaMA - Reddit](https://www.reddit.com/r/LocalLLaMA/comments/1k9rm65/qwen3_readmemd/?utm_source=chatgpt.com))  
> ⚠️ OpenRouter does **not** expose that flag today, so stick to the prompt tag when you’re using the hosted API.

---

## 3 “Hide but don’t stop” option

Like every model on the platform, Qwen obeys:

```jsonc
"reasoning": { "exclude": true }
```

This **suppresses the `reasoning` field in the JSON** while the model still thinks internally. Useful if you just want a cleaner payload or cheaper bandwidth. ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

*(You’ll still pay for those hidden tokens, so the prompt tags are more cost-efficient if you truly don’t need CoT.)*

---

## 4 What about slug variants such as `:thinking`?

` :thinking` is a **static slug extension** for Gemini and Claude; OpenRouter’s FAQ lists it but not for Qwen. ([OpenRouter FAQ | Developer Documentation](https://openrouter.ai/docs/faq?utm_source=chatgpt.com))  
Trying `qwen/qwen3-30b-a3b:thinking` (or `…:no_think`) will return *404*—the model relies solely on the prompt/directive mechanism.

---

## 5 Older Qwen models (QwQ, Qwen 2.5)

* **QwQ-32B** is a dedicated reasoning sibling: it always thinks, but you can still hide the tokens with `reasoning.exclude:true`. ([Qwen: QwQ 32B (free) – Run with an API - OpenRouter](https://openrouter.ai/qwen/qwq-32b%3Afree/api?utm_source=chatgpt.com))  
* **Qwen 2.5-Instruct** has no thinking engine at all, so there is nothing to disable.

---

## 6 Complete OpenAI-python snippet

```python
from openai import OpenAI
client = OpenAI(base_url="https://openrouter.ai/api/v1",
                api_key="YOUR_OR_KEY")

def ask_qwen(prompt, thinking=False):
    tag = "/think" if thinking else "/no_think"
    messages = [
        {"role": "system", "content": tag},
        {"role": "user",   "content": prompt}
    ]
    return client.chat.completions.create(
        model="qwen/qwen3-14b:free",   # any Qwen-3 slug works
        messages=messages,
        # omit `reasoning` to save tokens entirely
    ).choices[0].message.content

print(ask_qwen("Give me three bullet-points about the Eiffel Tower.", thinking=False))
```

---

### Key take-aways

1. **Prompt tag = full shutdown** of Qwen reasoning; cheapest and fastest.  
2. `reasoning.exclude:true` only hides CoT; tokens are still billed.  
3. No slug variants (`:thinking`, `:free`) control reasoning for Qwen—use the tags.  
4. QwQ always reasons; older Qwen 2.x models never do.  

Follow these rules and you’ll have precise, predictable control over Qwen’s reasoning cost on OpenRouter.

-----

User:
For the models that always think (like Deepseek R1), is it possible to set the main max_tokens argument to 32000, while setting the reasoning max_tokens to be 0? Or does it always have a lower bound of 1024?

-----

Assistant:
**Bottom line:** you can set the *outer* `max_tokens` for DeepSeek-R1 (or any “always-thinking” model) as high as 32 000, but you **cannot shrink the reasoning slice to zero**.  
OpenRouter either ignores `reasoning.max_tokens` on DeepSeek-R1 (because the model does not expose a tunable CoT budget yet) or, if the field is ever enabled, will clamp it to the platform-wide lower bound of **1 024 tokens**.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Model (deepseek-reasoner) | DeepSeek API Docs](https://api-docs.deepseek.com/guides/reasoning_model))  

---

## Why you can’t give DeepSeek-R1 a reasoning budget of 0

### 1  OpenRouter’s global clamp  
OpenRouter’s docs specify that whenever `reasoning.max_tokens` is accepted *at all*, the value is forced into  
`max( min(requested, 32 000) , 1 024 )` – i.e. **the minimum is 1 024**.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  

### 2  DeepSeek-R1 does **not** (yet) implement `reasoning.max_tokens`  
DeepSeek’s own API guide says the CoT can grow to 32 K tokens and that “the parameter to control the CoT length (`reasoning_effort`) will be available soon.”  ([Reasoning Model (deepseek-reasoner) | DeepSeek API Docs](https://api-docs.deepseek.com/guides/reasoning_model))  
Community tests confirm that supplying either `reasoning.effort` or `reasoning.max_tokens` is simply ignored.  ([How to stop openrouter/deepseek/deepseek-r1 from thinking in thousands of tokens ? · Issue #3803 · Aider-AI/aider · GitHub](https://github.com/Aider-AI/aider/issues/3803))  

### 3  What happens if you send `"reasoning": { "max_tokens": 0 }`?

| Situation | Result |
|-----------|--------|
| **OpenRouter today** | Parameter is ignored → R1 allocates its default internal budget (often several k tokens). |
| **Future (if R1 starts honouring it)** | Request is rejected or silently promoted to 1 024, because 0 < 1 024 lower bound.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens)) |

---

## Practical ways to keep costs down

1. **Hide the CoT instead of trying to disable it**  
   ```jsonc
   "reasoning": { "exclude": true }
   ```  
   This strips the `reasoning` field from the JSON, saving bandwidth and log clutter, but the thinking tokens are still counted for billing.  ([How to stop openrouter/deepseek/deepseek-r1 from thinking in thousands of tokens ? · Issue #3803 · Aider-AI/aider · GitHub](https://github.com/Aider-AI/aider/issues/3803), [Reasoning Tokens for Thinking Models - OpenRouter](https://openrouter.ai/announcements/reasoning-tokens-for-thinking-models?utm_source=chatgpt.com))  

2. **Cap total output with the outer `max_tokens`**  
   You can safely do  
   ```jsonc
   "max_tokens": 32000
   ```  
   R1 will stop when either its CoT + answer hits that ceiling **or** when it decides it is done, whichever comes first.  ([deepseek-ai/DeepSeek-R1 · Hugging Face](https://huggingface.co/deepseek-ai/DeepSeek-R1))  

3. **Switch models if you truly need zero reasoning**  
   Gemini-2.5 *without* the `:thinking` suffix or plain Claude-3 slugs emit no CoT at all, so you pay only for the answer.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter](https://openrouter.ai/docs/use-cases/reasoning-tokens?utm_source=chatgpt.com))  

---

## Code snapshot

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OR_KEY",
)

messages = [{"role": "user", "content": "Explain merge sort in one paragraph."}]

# DeepSeek-R1 with hidden (but unavoidable) reasoning
resp = client.chat.completions.create(
    model="deepseek/deepseek-r1",
    messages=messages,
    max_tokens=32000,          # total ceiling
    reasoning={"exclude": True}  # hides CoT, does NOT set it to zero
)
print(resp.choices[0].message.content)
```

---

### Key take-aways

* `reasoning.max_tokens: 0` is invalid; the floor is 1 024 tokens wherever the knob is supported.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens))  
* DeepSeek-R1 currently ignores **all** reasoning-budget knobs, so the only lever you have is the outer `max_tokens` and the `exclude` flag.  ([Reasoning Model (deepseek-reasoner) | DeepSeek API Docs](https://api-docs.deepseek.com/guides/reasoning_model), [How to stop openrouter/deepseek/deepseek-r1 from thinking in thousands of tokens ? · Issue #3803 · Aider-AI/aider · GitHub](https://github.com/Aider-AI/aider/issues/3803))  
* If you need absolutely no chain-of-thought—and to pay for none—use a model that offers a genuine non-thinking variant instead.  ([Reasoning Tokens | Enhanced AI Model Reasoning with OpenRouter | OpenRouter | Documentation](https://openrouter.ai/docs/use-cases/reasoning-tokens), [When querying R1 through OpenRouter, do you guys get reasoning ...](https://www.reddit.com/r/LocalLLaMA/comments/1idsaah/when_querying_r1_through_openrouter_do_you_guys/?utm_source=chatgpt.com))