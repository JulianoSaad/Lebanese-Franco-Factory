"""Lightweight record validation."""

from __future__ import annotations

from typing import Any


def validate_records(records: list[dict[str, Any]], family: str) -> dict[str, Any]:
    errors: list[str] = []
    for i, row in enumerate(records):
        if "id" not in row:
            errors.append(f"row {i}: missing id")
            continue
        if family == "conversion":
            for key in ("direction", "source", "target"):
                if not row.get(key):
                    errors.append(f"{row.get('id')}: missing {key}")
        elif family == "chat_sft":
            messages = row.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                errors.append(f"{row.get('id')}: messages must have >= 2 turns")
            else:
                for msg in messages:
                    if msg.get("role") not in {"user", "assistant", "system"}:
                        errors.append(f"{row.get('id')}: bad role {msg.get('role')!r}")
                    if not msg.get("content"):
                        errors.append(f"{row.get('id')}: empty content")
    return {
        "ok": not errors,
        "checked": len(records),
        "errors": errors,
        "error_count": len(errors),
    }
