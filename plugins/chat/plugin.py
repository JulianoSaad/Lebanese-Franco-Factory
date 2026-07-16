"""Chat SFT plugin — template + dictionary pack conversations."""

from __future__ import annotations

import json
import random
from typing import Any

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.dictionary.loader import iter_entries

PLUGIN = {
    "name": "chat",
    "family": "chat_sft",
    "version": "0.2.0",
    "datasets": ["chat_sft", "casual_chat", "office", "football"],
}


def _load_templates(domain: str) -> list[dict[str, Any]]:
    path = repo_root() / "data" / "templates" / "chat" / f"{domain}.json"
    if not path.exists():
        path = repo_root() / "data" / "templates" / "chat" / "casual_chat.json"
    return json.loads(path.read_text(encoding="utf-8"))


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    domain = config.get("domain") or "casual_chat"
    packs = config.get("dictionary_packs") or ["greetings", "emotions", "verbs"]
    rng = random.Random(seed)

    templates = _load_templates(domain)
    entries = iter_entries(packs)
    franco_words = [e["franco"][0] for e in entries if e.get("franco")]

    rows: list[dict[str, Any]] = []
    for i in range(size):
        tmpl = templates[i % len(templates)]
        user = tmpl["user"].format(
            greeting=rng.choice(franco_words),
            word=rng.choice(franco_words),
        )
        assistant = tmpl["assistant"].format(
            greeting=rng.choice(franco_words),
            word=rng.choice(franco_words),
        )
        user_u = f"{user} #{i+1}"
        assistant_u = f"{assistant} #{i+1}"
        rows.append(
            {
                "id": f"chat_{domain}_{i + 1:06d}",
                "family": "chat_sft",
                "domain": domain,
                "language": config.get("language", "lebanese_franco"),
                "messages": [
                    {"role": "user", "content": user_u},
                    {"role": "assistant", "content": assistant_u},
                ],
                "meta": {
                    "seed": seed,
                    "plugin": "chat",
                    "template_id": tmpl.get("id", "unknown"),
                    "dictionary_packs": packs,
                },
            }
        )
    return rows


def register(registry) -> None:
    registry.add_generator("chat", generate)
    registry.add_generator("chat_sft", generate)
    registry.add_generator("casual_chat", generate)
    registry.add_generator("office", generate)
    registry.add_generator("football", generate)
