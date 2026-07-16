"""Exact and light near-duplicate removal."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[!]{2,}", "!", text)
    text = re.sub(r"[?]{2,}", "?", text)
    return text


def _fingerprint(record: dict[str, Any]) -> str:
    family = record.get("family")
    if family == "chat_sft":
        payload = "||".join(
            f"{m.get('role')}:{_normalize_text(m.get('content', ''))}"
            for m in record.get("messages", [])
        )
    elif family in {"conversion", "spelling"}:
        payload = f"{record.get('direction') or record.get('kind')}|{_normalize_text(str(record.get('source', '')))}|{_normalize_text(str(record.get('target', '')))}"
    elif family == "instruction":
        payload = f"{record.get('task')}|{_normalize_text(str(record.get('input', '')))}|{_normalize_text(str(record.get('output', '')))}"
    else:
        payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def dedupe_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (kept, dropped) where dropped includes reason."""
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for row in records:
        fp = _fingerprint(row)
        if fp in seen:
            dropped.append({**row, "_drop_reason": "duplicate"})
            continue
        seen.add(fp)
        kept.append(row)
    return kept, dropped
