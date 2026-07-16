"""Apply human_feedback.jsonl back into the phrase lexicon (v0.2 loop)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lebanese_franco_factory.core.paths import repo_root, rules_dir


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
    """
    lexicon_path = lexicon_path or (rules_dir() / "phrase_lexicon.json")
    feedback = load_feedback(feedback_path)
    lexicon: list[dict[str, str]] = json.loads(lexicon_path.read_text(encoding="utf-8"))

    # index by arabic / franco for upsert
    by_ar = {row["arabic"]: i for i, row in enumerate(lexicon) if row.get("arabic")}
    added = updated = skipped = 0

    for item in feedback:
        decision = item.get("decision")
        if decision == "reject":
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
    return {"added": added, "updated": updated, "skipped": skipped, "feedback_rows": len(feedback)}
