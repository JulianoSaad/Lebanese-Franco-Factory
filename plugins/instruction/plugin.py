"""Instruction plugin — explain / summarize / rewrite in Lebanese Franco."""

from __future__ import annotations

import json
import random
from typing import Any

from lebanese_franco_factory.core.paths import rules_dir

PLUGIN = {
    "name": "instruction",
    "family": "instruction",
    "version": "0.1.0",
    "datasets": ["explain", "summarize", "rewrite", "instruction"],
}

_TASK_PROMPTS = {
    "explain": "sharhili hayda b franco lebneni:",
    "summarize": "lakhkhisli hayda b jumle wzire:",
    "rewrite": "a3id kitabit hayda b tari2a aktar tabi3iyye:",
}


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    task = config.get("task") or config.get("name") or "explain"
    if task == "instruction":
        task = "explain"
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    rng = random.Random(seed)
    lexicon = json.loads((rules_dir() / "phrase_lexicon.json").read_text(encoding="utf-8"))
    prompt = _TASK_PROMPTS[task]

    rows: list[dict[str, Any]] = []
    for i in range(size):
        item = lexicon[i % len(lexicon)] if i < len(lexicon) else rng.choice(lexicon)
        src = item["franco"]
        if task == "explain":
            output = f"{src} ya3ne: {item.get('english', src)}"
        elif task == "summarize":
            output = src
        else:
            # rewrite: prefer a spelling variant-ish mild change
            output = src.replace("ak", "ek") if "ak" in src else src
        inp = src if task != "explain" else item.get("arabic", src)
        rows.append(
            {
                "id": f"instruction_{task}_{i + 1:06d}",
                "family": "instruction",
                "task": task,
                "instruction": prompt,
                "input": f"{inp} #{i+1}",
                "output": f"{output} #{i+1}",
                "meta": {"seed": seed, "plugin": "instruction"},
            }
        )
    return rows


def register(registry) -> None:
    registry.add_generator("instruction", generate)
    for name in ("explain", "summarize", "rewrite"):
        registry.add_generator(name, generate)
