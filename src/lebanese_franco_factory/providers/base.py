"""Provider ABC — all backends share one API."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    """Common interface for model-assisted generation and evaluation."""

    name: str

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Return assistant text for chat messages."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs: Any) -> str:
        """Return a text completion for a prompt."""

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{self.__class__.__name__} name={self.name!r}>"


class NotConfiguredProvider(Provider):
    """Placeholder used until a real provider is selected."""

    name = "none"

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        raise RuntimeError("No provider configured. Rule-based generation does not need one.")

    def complete(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("No provider configured. Rule-based generation does not need one.")
