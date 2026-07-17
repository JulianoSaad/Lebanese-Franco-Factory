"""Ollama provider adapter — same Provider ABC as OpenAI/vLLM/etc."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from lebanese_franco_factory.providers.base import Provider


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(
        self,
        model: str = "qwen2.5",
        host: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = float(timeout)

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
            with urllib.request.urlopen(req, timeout=kwargs.get("timeout", self.timeout)) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama not reachable at {self.host}: {exc}") from exc
        return data.get("response", "")

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        prompt = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        prompt += "\nassistant:"
        return self.complete(prompt, **kwargs)
