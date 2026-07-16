"""Hugging Face Inference / local pipeline provider stub."""

from __future__ import annotations

from typing import Any

from lebanese_franco_factory.providers.base import Provider


class HuggingFaceProvider(Provider):
    name = "huggingface"

    def __init__(self, model: str = "Qwen/Qwen2.5-0.5B-Instruct") -> None:
        self.model = model
        self._pipe = None

    def _ensure(self) -> None:
        if self._pipe is not None:
            return
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install transformers to use HuggingFaceProvider") from exc
        self._pipe = pipeline("text-generation", model=self.model)

    def complete(self, prompt: str, **kwargs: Any) -> str:
        self._ensure()
        assert self._pipe is not None
        out = self._pipe(prompt, max_new_tokens=kwargs.get("max_new_tokens", 64))
        return out[0]["generated_text"]

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        prompt = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
        prompt += "\nassistant:"
        return self.complete(prompt, **kwargs)
