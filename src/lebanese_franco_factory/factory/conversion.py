"""Rule-based conversion using the phrase lexicon."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from lebanese_franco_factory.core.paths import rules_dir

Direction = Literal[
    "arabic_to_franco",
    "franco_to_arabic",
    "english_to_franco",
    "franco_to_english",
]


@lru_cache(maxsize=1)
def _lexicon() -> list[dict[str, str]]:
    path = rules_dir() / "phrase_lexicon.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _index(source_key: str, target_key: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in _lexicon():
        src = row.get(source_key)
        tgt = row.get(target_key)
        # First entry wins — preserves canonical golden pairs at the top of the lexicon.
        if src and tgt and src not in mapping:
            mapping[src] = tgt
    return mapping


def convert(text: str, direction: Direction) -> str:
    """Convert a known phrase. Raises KeyError if not in lexicon."""
    key_map = {
        "arabic_to_franco": ("arabic", "franco"),
        "franco_to_arabic": ("franco", "arabic"),
        "english_to_franco": ("english", "franco"),
        "franco_to_english": ("franco", "english"),
    }
    source_key, target_key = key_map[direction]
    mapping = _index(source_key, target_key)
    if text not in mapping:
        raise KeyError(f"No lexicon entry for {direction!r}: {text!r}")
    return mapping[text]


def convert_or_none(text: str, direction: Direction) -> str | None:
    try:
        return convert(text, direction)
    except KeyError:
        return None
