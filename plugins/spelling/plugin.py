"""Spelling robustness plugin — typos, variants, abbreviations."""

from __future__ import annotations

import json
import random
from typing import Any

from lebanese_franco_factory.core.paths import rules_dir

PLUGIN = {
    "name": "spelling",
    "family": "spelling",
    "version": "0.1.0",
    "datasets": ["typos", "variants", "abbreviations", "spelling"],
}


def _load_json(name: str) -> dict[str, Any]:
    return json.loads((rules_dir() / name).read_text(encoding="utf-8"))


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    kind = config.get("kind") or config.get("name") or "typos"
    if kind == "spelling":
        kind = "typos"
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    rng = random.Random(seed)

    rows: list[dict[str, Any]] = []
    if kind == "variants":
        variants = _load_json("spelling_variants.json")
        pairs = [(canon, v) for canon, vs in variants.items() for v in vs]
        for i in range(size):
            canon, variant = pairs[i % len(pairs)] if pairs else ("kifak", "keefak")
            if i >= len(pairs):
                canon, variant = rng.choice(pairs)
            rows.append(
                {
                    "id": f"spelling_variants_{i + 1:06d}",
                    "family": "spelling",
                    "kind": "variants",
                    "source": f"{variant} #{i+1}",
                    "target": f"{canon} #{i+1}",
                    "meta": {"seed": seed, "plugin": "spelling"},
                }
            )
    elif kind == "abbreviations":
        abbr = _load_json("abbreviations.json")
        pairs = list(abbr.items())
        for i in range(size):
            short, full = pairs[i % len(pairs)]
            if i >= len(pairs):
                short, full = rng.choice(pairs)
            rows.append(
                {
                    "id": f"spelling_abbreviations_{i + 1:06d}",
                    "family": "spelling",
                    "kind": "abbreviations",
                    "source": f"{short} #{i+1}",
                    "target": f"{full} #{i+1}",
                    "meta": {"seed": seed, "plugin": "spelling"},
                }
            )
    else:  # typos
        lexicon = json.loads((rules_dir() / "phrase_lexicon.json").read_text(encoding="utf-8"))
        for i in range(size):
            item = lexicon[i % len(lexicon)]
            text = item["franco"]
            # controlled character noise
            if len(text) > 3 and rng.random() < 0.8:
                pos = rng.randint(0, len(text) - 1)
                if text[pos].isalpha():
                    noisy = text[:pos] + text[pos] + text[pos] + text[pos + 1 :]
                else:
                    noisy = text
            else:
                noisy = text.replace("a", "aa", 1) if "a" in text else text + " "
            rows.append(
                {
                    "id": f"spelling_typos_{i + 1:06d}",
                    "family": "spelling",
                    "kind": "typos",
                    "source": f"{noisy.strip()} #{i+1}",
                    "target": f"{text} #{i+1}",
                    "meta": {"seed": seed, "plugin": "spelling"},
                }
            )
    return rows


def register(registry) -> None:
    registry.add_generator("spelling", generate)
    for name in ("typos", "variants", "abbreviations"):
        registry.add_generator(name, generate)
