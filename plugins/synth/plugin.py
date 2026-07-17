"""Synth plugin — grow *genuinely varied* Franco phrases via an AI provider.

Unlike the rule-based ``conversion`` plugin (which cycles a fixed lexicon and
adds ``[i]`` prefixes to reach a target size), this plugin asks a real model
(Ollama / OpenAI / LiteLLM / vLLM / HF — any wired provider) to invent *new*
Lebanese-Franco phrases, then keeps only the ones not already in the lexicon.

Output rows are the ``conversion`` family (so the validator, review UI, and
exporter all handle them). Because the content is model-generated, every row is
tagged ``meta.needs_human = True`` and ``meta.source = "synth"`` so it routes
into the human-review queue **before** any training — never trained blind.

The prompt/parse helpers are pure functions so they can be unit-tested without
a live provider.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

from lebanese_franco_factory.core.paths import rules_dir

PLUGIN = {
    "name": "synth",
    "family": "conversion",
    "version": "0.1.0",
    "datasets": ["franco_synth"],
}

# source/target field per conversion direction
_DIRECTION_KEYS: dict[str, tuple[str, str]] = {
    "arabic_to_franco": ("arabic", "franco"),
    "franco_to_arabic": ("franco", "arabic"),
    "english_to_franco": ("english", "franco"),
    "franco_to_english": ("franco", "english"),
}

_AR_RE = re.compile(r"[؀-ۿ]")


def build_prompt(examples: list[dict[str, str]], n: int, batch_idx: int) -> str:
    """Few-shot prompt asking for ``n`` NEW Lebanese-Franco triples as JSON.

    ``batch_idx`` nudges the model toward a different slice of everyday life each
    batch, so successive calls don't converge on the same greetings.
    """
    themes = [
        "daily life and family",
        "food, coffee, and going out",
        "work, phone, and internet/telecom",
        "traffic, weather, and neighborhoods",
        "shopping, money, and prices",
        "feelings, plans, and small talk",
        "football, music, and weekend",
        "school, health, and appointments",
    ]
    theme = themes[batch_idx % len(themes)]
    shots = "\n".join(
        json.dumps(
            {"arabic": e["arabic"], "franco": e["franco"], "english": e.get("english", "")},
            ensure_ascii=False,
        )
        for e in examples
    )
    return (
        "You generate authentic LEBANESE dialect data — not Modern Standard "
        "Arabic, not Egyptian, not Gulf. 'Franco' (Arabizi) is Lebanese written "
        "in Latin letters and chat numerals (7=ح, 3=ع, 2=ء, 5=خ, 8=غ, 9=ق).\n\n"
        f"Here are real examples:\n{shots}\n\n"
        f"Now write {n} NEW, DIFFERENT everyday Lebanese phrases about "
        f"{theme}. Each must be natural spoken Lebanese, not a copy of the "
        "examples. Return ONLY a JSON array; each item has exactly the keys "
        '"arabic", "franco", "english". No commentary, no code fences.'
    )


def parse_pairs(text: str) -> list[dict[str, str]]:
    """Extract ``{arabic, franco, english}`` triples from raw model output.

    Tolerates code fences, surrounding prose, a JSON array, or JSONL. Skips any
    item missing Arabic script in ``arabic`` or an empty ``franco``.
    """
    if not text:
        return []
    cleaned = re.sub(r"```[a-zA-Z]*", "", text).replace("```", "").strip()

    candidates: list[Any] = []
    # 1) whole thing is JSON
    try:
        obj = json.loads(cleaned)
        candidates = obj if isinstance(obj, list) else [obj]
    except json.JSONDecodeError:
        # 2) first [...] block
        m = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if m:
            try:
                candidates = json.loads(m.group(0))
            except json.JSONDecodeError:
                candidates = []
        # 3) JSONL fallback
        if not candidates:
            for line in cleaned.splitlines():
                line = line.strip().rstrip(",")
                if line.startswith("{") and line.endswith("}"):
                    try:
                        candidates.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    out: list[dict[str, str]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        ar = str(item.get("arabic", "")).strip()
        fr = str(item.get("franco", "")).strip()
        en = str(item.get("english", "")).strip()
        if not fr or not _AR_RE.search(ar):
            continue
        out.append({"arabic": ar, "franco": fr, "english": en})
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _to_row(triple: dict[str, str], direction: str, idx: int, meta_base: dict[str, Any]) -> dict:
    source_key, target_key = _DIRECTION_KEYS[direction]
    return {
        "id": f"synth_{direction}_{idx + 1:06d}",
        "family": "conversion",
        "direction": direction,
        "source": triple[source_key],
        "target": triple[target_key],
        "meta": {**meta_base, "arabic": triple["arabic"], "franco": triple["franco"]},
    }


def generate(config: dict[str, Any]) -> list[dict[str, Any]]:
    from lebanese_franco_factory.providers.registry import get_provider

    direction = config.get("direction") or "arabic_to_franco"
    if direction not in _DIRECTION_KEYS:
        raise ValueError(f"synth: unknown direction {direction!r}")
    size = int(config.get("size", 100))
    seed = int(config.get("seed", 42))
    batch_size = int(config.get("batch_size", 20))
    few_shot = int(config.get("few_shot", 6))
    provider_name = config.get("provider", "ollama")
    if provider_name in (None, "none"):
        raise ValueError(
            "synth requires an AI provider (e.g. provider: ollama). "
            "Rule-based variety is what the 'conversion' plugin already does."
        )
    provider = get_provider(
        provider_name,
        **{k: v for k, v in {
            "model": config.get("model") or config.get("provider_model"),
            "host": config.get("host") or config.get("provider_host"),
        }.items() if v is not None},
    )

    lexicon = json.loads((rules_dir() / "phrase_lexicon.json").read_text(encoding="utf-8"))
    rng = random.Random(seed)
    # existing phrases we must NOT reproduce (dedup on the Franco surface form)
    seen: set[str] = {_norm(e.get("franco", "")) for e in lexicon}

    meta_base = {
        "source": "synth",
        "needs_human": True,
        "provider": provider_name,
        "model": config.get("model") or config.get("provider_model"),
    }

    collected: list[dict[str, str]] = []
    max_batches = max(4, (size // max(1, batch_size)) * 3 + 4)  # bounded — provider may under-deliver
    for batch_idx in range(max_batches):
        if len(collected) >= size:
            break
        shots = rng.sample(lexicon, min(few_shot, len(lexicon)))
        prompt = build_prompt(shots, batch_size, batch_idx)
        try:
            text = provider.complete(prompt)
        except Exception as exc:  # provider unreachable / errored
            raise RuntimeError(
                f"synth: provider {provider_name!r} failed on batch {batch_idx}: {exc}"
            ) from exc
        for triple in parse_pairs(text):
            key = _norm(triple["franco"])
            if key in seen:
                continue
            seen.add(key)
            collected.append(triple)
            if len(collected) >= size:
                break

    return [_to_row(t, direction, i, meta_base) for i, t in enumerate(collected)]


def register(registry) -> None:
    registry.add_generator("synth", generate)
    registry.add_generator("franco_synth", generate)
