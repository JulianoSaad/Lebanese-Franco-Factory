"""LiteLLM provider — optional dependency, same Provider API."""

from __future__ import annotations

from typing import Any

from lebanese_franco_factory.providers.base import Provider


class LiteLLMProvider(Provider):
    name = "litellm"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model

    def complete(self, prompt: str, **kwargs: Any) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        try:
            from litellm import completion  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install litellm to use LiteLLMProvider") from exc
        resp = completion(model=kwargs.get("model", self.model), messages=messages)
        return resp.choices[0].message.content or ""
