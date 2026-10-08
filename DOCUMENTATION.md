# Technical Architecture & Engineering Documentation
## Module 3: LLM APIs & Application Development

---

## 1. Executive Summary & Design Principles

The **NexusAI Chat Studio** architecture is designed around four enterprise engineering principles:
1. **Decoupled Provider Orchestration:** Application layers interact with an abstract interface (`UnifiedLLMClient`) rather than proprietary SDKs directly.
2. **Deterministic Context Management:** Memory is strictly controlled via an algorithmic sliding window to bound latency and API cost.
3. **Fail-Safe Resilience:** Transient HTTP 429/503 errors trigger exponential backoff with randomized jitter, preventing cascading thundering herd failures.
4. **Transparent Token Economics:** Every request is accounted for against an active session budget with audit logging.

---

## 2. Conversation Management & The Sliding Window Algorithm

### The Context Window Problem
Large Language Models are strictly stateless. To maintain conversational continuity, applications must resubmit the entire historical sequence with each subsequent prompt. In naive implementations:
- Prompt tokens grow quadratically ($O(N^2)$) relative to conversational length.
- Latency escalates linearly.
- Conversations inevitably breach the model's hard context limit, producing catastrophic HTTP 400 `context_length_exceeded` errors.

### Algorithmic Solution
The `ConversationManager` maintains two distinct memory structures:
1. **Immutable Anchor:** The `system` message containing the persona and operational boundaries is anchored at index 0 and protected from eviction.
2. **Volatile Buffer:** Dialogue turns `[User, Assistant, User, Assistant, ...]` stored sequentially.

```python
def apply_sliding_window_if_needed(self) -> int:
    pruned_count = 0
    effective_limit = max(256, self.max_context_tokens - self.max_tokens)
    
    while len(self.history) > 2 and self.estimate_total_tokens() > effective_limit:
        self.history.pop(0)  # Evict oldest turn
        pruned_count += 1
        
    return pruned_count
```

---

## 3. Parameter Optimization Matrix

| Parameter | Recommended Range | Mathematical Meaning | Production Use Case |
| :--- | :--- | :--- | :--- |
| **`temperature`** | `0.0 – 0.3` | Low entropy, high probability token selection | Deterministic code review, JSON schemas, calculations |
| **`temperature`** | `0.6 – 0.8` | Balanced distribution | General conversational dialogue, mentoring, explanations |
| **`temperature`** | `1.0 – 1.4` | High entropy, diverse token sampling | Creative brainstorming, diverse copywriting |
| **`top_p`** | `0.90 – 0.95` | Cumulative probability nucleus filtering | Filters low-probability tail tokens without sacrificing diversity |
| **`max_tokens`** | `512 – 2048` | Hard ceiling on generated response length | Budget enforcement & protection against runaway loops |

---

## 4. Structured JSON Extraction & Pydantic Validation

LLMs naturally produce conversational filler ("Sure! Here is the JSON:"). To ensure production services receive parseable payloads:
1. **Schema Injection:** The Pydantic model's JSON Schema is extracted via `.model_json_schema()` and injected into the system prompt with strict negative constraints.
2. **Regex Extraction:** The response is passed through multi-pattern extractors searching for Markdown code fences (````json ... ````) or outermost `{...}` boundaries.
3. **Self-Healing Syntax Repair:** Trailing commas (`[1, 2, 3, ]` or `{"a": 1, }`), the leading cause of JSON parser failures, are automatically sanitized before deserialization.
4. **Pydantic Validation:** The cleaned dictionary is parsed through `model_validate()`, raising typed schema violations if mandatory fields or ranges are infringed.

---

## 5. Resilient Error Handling & Full Jitter Exponential Backoff

When LLM providers encounter capacity bottlenecks, they emit HTTP 429 `rate_limit_exceeded`. Immediate synchronous retries exacerbate server saturation. NexusAI employs exponential backoff with **Full Jitter**:

$$T_{\text{sleep}} = \text{delay} \times (1.0 + \text{random}(0.0, 0.2))$$
$$\text{delay}_{i+1} = \text{delay}_i \times 2$$

This guarantees that parallel requests retry asynchronously over time rather than synchronizing on clock ticks.

---

## 6. Token Economics & Cost Optimization Benchmarks

The financial difference between models is substantial. The cost engine implements exact weighting:

$$\text{Cost}_{\text{turn}} = \left(\frac{T_{\text{prompt}}}{10^6} \times P_{\text{prompt}}\right) + \left(\frac{T_{\text{completion}}}{10^6} \times P_{\text{completion}}\right)$$

### Economic Comparison (100,000 Turns @ 500 Input / 300 Output tokens):
- **Flagship (GPT-4o):** $(50M \times \$2.50) + (30M \times \$10.00) = \$125 + \$300 = \mathbf{\$425.00}$
- **Efficient Tier (GPT-4o-mini):** $(50M \times \$0.15) + (30M \times \$0.60) = \$7.50 + \$18.00 = \mathbf{\$25.50}$ (94% Savings!)
- **Ultra-Fast (Gemini 1.5 Flash):** $(50M \times \$0.075) + (30M \times \$0.30) = \$3.75 + \$9.00 = \mathbf{\$12.75}$ (97% Savings!)

The application defaults to `gpt-4o-mini` to maximize student budget sustainability while delivering near-flagship intelligence.
