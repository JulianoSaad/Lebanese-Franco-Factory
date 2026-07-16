"""Copy this folder to create a new domain plugin (e.g. plugins/medical)."""

from __future__ import annotations

from typing import Any

PLUGIN = {
    "name": "_template",
    "family": "chat_sft",
    "version": "0.0.0",
    "datasets": [],
}


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    raise NotImplementedError("Replace _template with a real plugin")


def register(registry) -> None:
    # Intentionally not registered — folder name starts with underscore and is skipped.
    return
