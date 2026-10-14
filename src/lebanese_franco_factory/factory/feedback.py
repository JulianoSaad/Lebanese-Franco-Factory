"""Apply human_feedback.jsonl back into the phrase lexicon (v0.2 loop)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lebanese_franco_factory.core.paths import repo_root, rules_dir
from lebanese_franco_factory.factory.cleaner.arabizi import (
    franco_violations,
    msa_vocabulary,
    normalize_franco,
)

# A recorded correction only counts as gold if it follows the spelling convention
# (docs/ARABIZI_CONVENTION.md). 24 of the 45 corrections in human_feedback.jsonl rewrote
# Lebanese into Modern Standard Arabic in Latin letters ("ana mut3ab" -> "ana mut3abaton",
# "alshar3 mazdaham" -> "al touroukat mouzdahima"); training on those teaches MSA, the
# opposite of this project's target. They are dropped here by rule, not by a hand-made list.
# Mechanical breaks are repaired by the normalizer, so they never cost us a row. What cannot
# be repaired is vocabulary: 24 of the 45 recorded corrections rewrote Lebanese into MSA.
UNFIXABLE = ("arabic_in_franco",)


def gold_spelling(franco: str) -> str:
    """The spelling that would enter gold: the convention-normalized form."""
    return normalize_franco(franco)


def gold_quality(franco: str) -> list[str]:
    """Why this spelling cannot be gold, after normalizing (empty list = acceptable)."""
    fixed = normalize_franco(franco)
    # Check both forms: normalizing "alhadiqa" to "l hadiqa" would otherwise hide the MSA word.
    reasons = msa_vocabulary(franco) + msa_vocabulary(fixed)
    reasons += [v for v in franco_violations(fixed) if v in UNFIXABLE or v == "msa_ending"]
    return sorted(set(reasons))


def feedback_file() -> Path:
    return repo_root() / "feedback" / "human_feedback.jsonl"


def load_feedback(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or feedback_file()
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def apply_feedback_to_lexicon(
    feedback_path: Path | None = None,
    lexicon_path: Path | None = None,
) -> dict[str, int]:
    """
    Merge accepted/edited conversion pairs into phrase_lexicon.json.

    - decision=correct → keep generated as franco (or target)
    - decision=edit → use corrected
    - decision=reject → skip (optionally blacklist later)

    A row is also skipped when it carries ``excluded_from_gold`` or when its spelling breaks
    the convention; those are counted as ``off_convention`` so callers can report them.
    """
    lexicon_path = lexicon_path or (rules_dir() / "phrase_lexicon.json")
    feedback = load_feedback(feedback_path)
    lexicon: list[dict[str, str]] = json.loads(lexicon_path.read_text(encoding="utf-8"))

    # First entry wins (matches conversion index). Keep updates on the canonical row.
    by_ar: dict[str, int] = {}
    for i, row in enumerate(lexicon):
        arabic = row.get("arabic")
        if arabic and arabic not in by_ar:
            by_ar[arabic] = i
    added = updated = skipped = off_convention = 0

    for item in feedback:
        decision = item.get("decision")
        if decision == "reject" or item.get("excluded_from_gold"):
            skipped += 1
            continue
        original = (item.get("original") or "").strip()
        generated = (item.get("generated") or "").strip()
        corrected = (item.get("corrected") or generated).strip()
        if decision == "correct":
            franco = generated
        elif decision == "edit":
            franco = corrected
        else:
            skipped += 1
            continue
        if not original or not franco:
            skipped += 1
            continue
        if gold_quality(franco):
            off_convention += 1
            continue
        franco = gold_spelling(franco)  # store the convention spelling, not the raw one

        # Heuristic: Arabic script in original → arabic_to_franco
        if any("\u0600" <= ch <= "\u06FF" for ch in original):
            arabic, target_franco = original, franco
            if arabic in by_ar:
                lexicon[by_ar[arabic]]["franco"] = target_franco
                updated += 1
            else:
                lexicon.append({"arabic": arabic, "franco": target_franco, "english": ""})
                by_ar[arabic] = len(lexicon) - 1
                added += 1
        else:
            # treat as franco canonicalization note
            skipped += 1

    lexicon_path.write_text(json.dumps(lexicon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # clear conversion cache if loaded
    try:
        from lebanese_franco_factory.factory import conversion as conv

        conv._lexicon.cache_clear()
    except Exception:
        pass
    return {"added": added, "updated": updated, "skipped": skipped,
            "off_convention": off_convention, "feedback_rows": len(feedback)}
