"""CI gate: conversion must match tests/100_expected_outputs.json."""

from __future__ import annotations

import json
from pathlib import Path

from lebanese_franco_factory.factory.conversion import convert

GOLDEN = Path(__file__).resolve().parent / "100_expected_outputs.json"


def test_golden_file_has_100_rows() -> None:
    rows = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert len(rows) == 100


def test_all_golden_arabic_to_franco() -> None:
    rows = json.loads(GOLDEN.read_text(encoding="utf-8"))
    failures: list[str] = []
    for row in rows:
        got = convert(row["input"], row["direction"])
        if got != row["expected"]:
            failures.append(f"{row['id']}: expected {row['expected']!r}, got {got!r}")
    assert not failures, "\n".join(failures[:20])
