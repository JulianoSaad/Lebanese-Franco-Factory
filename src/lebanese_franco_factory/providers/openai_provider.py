"""OpenAI-compatible chat provider."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from lebanese_franco_factory.providers.base import Provider


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str, **kwargs: Any) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc
        return data["choices"][0]["message"]["content"]
