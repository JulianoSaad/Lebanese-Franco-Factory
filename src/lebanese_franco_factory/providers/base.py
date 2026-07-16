"""Provider protocol — model-agnostic interface (implementations later)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    name: str

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Return assistant text for a chat completion request."""

    def complete(self, prompt: str, **kwargs: Any) -> str:
        """Return text completion for a prompt."""


class NotConfiguredProvider:
    """Placeholder used until real providers are wired."""

    name = "none"

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        raise RuntimeError("No provider configured. Rule-based generation does not need one.")

    def complete(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("No provider configured. Rule-based generation does not need one.")
