# CivicPulse — AI Analyst architecture

## Design principle

The AI analyst is **grounded**, not a general chatbot: a user's question is never sent straight to the LLM for it to answer from "knowledge." Instead:

```
User question
    |
    v
FastAPI /api/v1/ai/ask
    |
    v
Tool selector — maps the question to ONE of a small, fixed set of
functions in ai/tools/ (NOT free-form SQL generation by the LLM)
    |
    v
The selected tool runs a parameterized, pre-written SQL query
against the warehouse and returns real numbers
    |
    v
Those numbers (only) are inserted into a prompt template
(ai/prompts/) and sent to Ollama
    |
    v
Ollama returns a natural-language explanation of the real numbers
```

## Why a fixed toolset instead of LLM-generated SQL

Local open-weight models (the kind Ollama runs well on consumer hardware) are noticeably weaker than frontier hosted models at reliably writing correct, safe SQL from a natural-language question, especially across multiple turns. A small fixed set of parameterized functions:

- `get_ward_summary(ward_code)`
- `get_top_hotspots(n)`
- `get_department_backlog()`
- `get_category_trend(category, period)`

is far more reliable, is trivially safe against SQL injection (parameters bound, not concatenated), and is easy to unit test independently of the LLM. The tradeoff — the analyst can only answer questions the toolset covers — is explicit and acceptable for this project's scope.

## Tool selection

For an MVP, tool selection can be a simple rule-based/keyword match (see `ai/tools/router.py` stub) before introducing LLM-based function calling. This keeps the system debuggable and gives you an honest fallback to describe in an interview: "I started with rule-based routing and the design leaves room to swap in LLM function-calling once the toolset is stable."

## Example

**Question:** "Why is Ward 12 high priority?"

**Retrieved data** (via `get_ward_summary("W12")`):
```
Complaints: 823
Growth: +34%
Critical: 91
Backlog: 218
Avg resolution: 16.2 days
Hotspots: 3
```

**Prompt sent to Ollama** (see `ai/prompts/ward_explainer.txt`): the retrieved numbers plus an instruction to explain, in plain language, why this ward would rank as high priority — explicitly told not to invent numbers not given to it.

**Output:** a short natural-language explanation referencing only the supplied figures.

## Preventing hallucination

- The LLM only ever sees numbers the tool layer retrieved in that same request — it has no database access itself.
- The prompt template explicitly instructs the model to use only the provided figures.
- Responses can be spot-checked by re-extracting any numbers the model states and diffing them against what was supplied, as a lightweight automated guardrail (see `ai/tools/verify.py` stub — optional, add if time allows).
