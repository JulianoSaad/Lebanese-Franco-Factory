"""Lightweight record validation using Pydantic schemas where applicable."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from lebanese_franco_factory.core.schemas import (
    ChatSFTRecord,
    ConversionRecord,
    InstructionRecord,
    SpellingRecord,
)


def validate_records(records: list[dict[str, Any]], family: str) -> dict[str, Any]:
    errors: list[str] = []
    model = {
        "chat_sft": ChatSFTRecord,
        "conversion": ConversionRecord,
        "spelling": SpellingRecord,
        "instruction": InstructionRecord,
    }.get(family)

    for i, row in enumerate(records):
        if model is None:
            if "id" not in row:
                errors.append(f"row {i}: missing id")
            continue
        try:
            model.model_validate(row)
        except ValidationError as exc:
            errors.append(f"{row.get('id', i)}: {exc.errors()[0]['msg']}")
    return {
        "ok": not errors,
        "checked": len(records),
        "errors": errors,
        "error_count": len(errors),
    }
