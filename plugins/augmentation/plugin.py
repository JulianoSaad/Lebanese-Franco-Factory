"""Augmentation plugin — independent paraphrases / digit-arabizi noise."""

from __future__ import annotations

import json
import random
from typing import Any

from lebanese_franco_factory.core.paths import rules_dir

PLUGIN = {
    "name": "augmentation",
    "family": "augmentation",
    "version": "0.1.0",
    "datasets": ["augmentation", "digit_noise"],
}


def _digitify(text: str, rng: random.Random) -> str:
    """Light Arabizi digit substitutions for robustness data."""
    repl = {"h": "7", "H": "7", "a": "2", "A": "2", "g": "8", "G": "8"}
    chars = list(text)
    for i, ch in enumerate(chars):
        if ch in repl and rng.random() < 0.35:
            chars[i] = repl[ch]
    return "".join(chars)


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    rng = random.Random(seed)
    lexicon = json.loads((rules_dir() / "phrase_lexicon.json").read_text(encoding="utf-8"))

    rows: list[dict[str, Any]] = []
    for i in range(size):
        item = lexicon[i % len(lexicon)]
        source = item["franco"]
        target = _digitify(source, rng)
        if target == source:
            target = source + " "  # still mark as augmented row uniqueness
        rows.append(
            {
                "id": f"augmentation_{i + 1:06d}",
                "family": "spelling",  # reuse spelling schema: source→target
                "kind": "typos",
                "source": f"{target.strip()} #{i+1}",
                "target": f"{source} #{i+1}",
                "meta": {
                    "seed": seed,
                    "plugin": "augmentation",
                    "augmentation": "digit_noise",
                },
            }
        )
    return rows


def register(registry) -> None:
    registry.add_generator("augmentation", generate)
    registry.add_generator("digit_noise", generate)
