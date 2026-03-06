from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict


def generate_with_provider(prompt: str, provider: str = "ollama", model: str = "qwen3:1.7b") -> str:
    """
    Currently supports:
    - ollama (default)
    - openai (optional)

    If provider is unknown, fallback to ollama.
    """

    provider = (provider or "ollama").lower().strip()

    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if key:
            return _openai_generate(prompt, model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), api_key=key)

    # default
    return _ollama_generate(prompt, model=os.getenv("OLLAMA_MODEL", model))


def _ollama_generate(prompt: str, model: str) -> str:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    url = f"{host}/api/generate"

    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return str(data.get("response", "")).strip()


def _openai_generate(prompt: str, model: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return str(data["choices"][0]["message"]["content"]).strip()