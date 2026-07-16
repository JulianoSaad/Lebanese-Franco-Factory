"""vLLM OpenAI-compatible server provider."""

from __future__ import annotations

from typing import Any

from lebanese_franco_factory.providers.openai_provider import OpenAIProvider


class VLLMProvider(OpenAIProvider):
    """Talks to a local vLLM server via the OpenAI-compatible API."""

    name = "vllm"

    def __init__(
        self,
        model: str = "default",
        base_url: str = "http://127.0.0.1:8000/v1",
        api_key: str = "EMPTY",
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url)

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        return super().chat(messages, **kwargs)
