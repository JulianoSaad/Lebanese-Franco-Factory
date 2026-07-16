"""Conversion plugin — arabic/franco/english phrase pairs."""

from __future__ import annotations

import json
import random
from typing import Any

from lebanese_franco_factory.core.paths import rules_dir
from lebanese_franco_factory.factory.conversion import Direction

PLUGIN = {
    "name": "conversion",
    "family": "conversion",
    "version": "0.1.0",
    "datasets": [
        "arabic_to_franco",
        "franco_to_arabic",
        "english_to_franco",
        "franco_to_english",
    ],
}

_DIRECTION_KEYS: dict[Direction, tuple[str, str]] = {
    "arabic_to_franco": ("arabic", "franco"),
    "franco_to_arabic": ("franco", "arabic"),
    "english_to_franco": ("english", "franco"),
    "franco_to_english": ("franco", "english"),
}


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    direction: Direction = config.get("direction") or config["name"]
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    rng = random.Random(seed)

    lexicon = json.loads((rules_dir() / "phrase_lexicon.json").read_text(encoding="utf-8"))
    source_key, target_key = _DIRECTION_KEYS[direction]

    rows: list[dict[str, Any]] = []
    for i in range(size):
        item = lexicon[i] if i < len(lexicon) else rng.choice(lexicon)
        rows.append(
            {
                "id": f"{direction}_{i + 1:06d}",
                "family": "conversion",
                "direction": direction,
                "source": item[source_key],
                "target": item[target_key],
                "meta": {"seed": seed, "plugin": "conversion"},
            }
        )
    return rows


def register(registry) -> None:
    registry.add_generator("conversion", generate)
    for name in PLUGIN["datasets"]:
        registry.add_generator(name, generate)
