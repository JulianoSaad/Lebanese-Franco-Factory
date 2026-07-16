"""Ollama provider adapter (optional; used for model-assisted generation later)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class OllamaProvider:
    name = "ollama"

    def __init__(self, model: str = "qwen2.5", host: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.host = host.rstrip("/")

    def complete(self, prompt: str, **kwargs: Any) -> str:
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama not reachable at {self.host}: {exc}") from exc
        return data.get("response", "")

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        # Flatten to a simple prompt for broad compatibility
        prompt = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        prompt += "\nassistant:"
        return self.complete(prompt, **kwargs)
