"""
Rule-based tool router for the AI analyst.

Deliberately NOT an LLM writing free-form SQL — see docs/ai-architecture.md
for why. This maps a question to one of a small fixed set of grounded
tools, each of which runs a parameterized query against the warehouse.

MVP: simple keyword matching. Swap in LLM function-calling later once
the toolset itself is stable and well-tested.
"""
from typing import Callable

from ai.tools import queries


TOOLS: dict[str, Callable] = {
    "ward_summary": queries.get_ward_summary,
    "top_hotspots": queries.get_top_hotspots,
    "department_backlog": queries.get_department_backlog,
    "category_trend": queries.get_category_trend,
}


def route(question: str) -> tuple[str, dict]:
    """
    Return (tool_name, kwargs) for a natural-language question.
    Raises ValueError if no tool matches — the API layer should turn
    this into a friendly "I can't answer that yet" response rather
    than falling back to an ungrounded LLM answer.
    """
    q = question.lower()

    if "ward" in q:
        ward_code = _extract_ward_code(q)
        if ward_code:
            return "ward_summary", {"ward_code": ward_code}

    if "hotspot" in q or "worst affected" in q:
        return "top_hotspots", {"n": 5}

    if "backlog" in q or "department" in q:
        return "department_backlog", {}

    if "trend" in q or "increasing" in q or "increased" in q:
        return "category_trend", {"period": "30d"}

    raise ValueError(f"No grounded tool matches question: {question!r}")


def _extract_ward_code(q: str) -> str | None:
    """Very small heuristic — replace with a proper NER/regex pass as needed."""
    import re
    match = re.search(r"ward\s*(\d+)", q)
    if match:
        return f"W{match.group(1)}"
    return None
