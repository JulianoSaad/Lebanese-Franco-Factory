"""Provider registry — resolve by name."""

from __future__ import annotations

from typing import Any

from lebanese_franco_factory.providers.base import NotConfiguredProvider, Provider
from lebanese_franco_factory.providers.huggingface import HuggingFaceProvider
from lebanese_franco_factory.providers.litellm_provider import LiteLLMProvider
from lebanese_franco_factory.providers.ollama import OllamaProvider
from lebanese_franco_factory.providers.openai_provider import OpenAIProvider
from lebanese_franco_factory.providers.vllm_provider import VLLMProvider

_PROVIDERS: dict[str, type[Provider]] = {
    "none": NotConfiguredProvider,
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "litellm": LiteLLMProvider,
    "vllm": VLLMProvider,
    "huggingface": HuggingFaceProvider,
    "hf": HuggingFaceProvider,
}


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider(name: str | None = None, **kwargs: Any) -> Provider:
    key = (name or "none").lower()
    if key not in _PROVIDERS:
        raise KeyError(f"Unknown provider {name!r}. Available: {', '.join(available_providers())}")
    return _PROVIDERS[key](**kwargs) if key != "none" else NotConfiguredProvider()
