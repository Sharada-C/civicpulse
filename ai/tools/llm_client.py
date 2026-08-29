"""
Thin wrapper around a local Ollama instance. No paid API involved.
"""
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"  # swap for whatever open-weight model you pull locally


def explain(prompt: str, model: str = MODEL) -> str:
    """Send a fully-formed, data-grounded prompt to Ollama and return the text response."""
    response = httpx.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()
