"""Prepare mixed JSONL for LoRA/SFT training."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def record_to_messages(row: dict[str, Any]) -> list[dict[str, str]]:
    family = row.get("family")
    if family == "chat_sft":
        return [{"role": m["role"], "content": m["content"]} for m in row["messages"]]
    if family == "conversion":
        return [
            {
                "role": "user",
                "content": f"Convert ({row['direction']}): {row['source']}",
            },
            {"role": "assistant", "content": row["target"]},
        ]
    if family == "spelling":
        return [
            {"role": "user", "content": f"Fix Lebanese Franco ({row['kind']}): {row['source']}"},
            {"role": "assistant", "content": row["target"]},
        ]
    if family == "instruction":
        return [
            {
                "role": "user",
                "content": f"{row['instruction']}\n{row['input']}",
            },
            {"role": "assistant", "content": row["output"]},
        ]
    raise ValueError(f"Unsupported family: {family}")


def collect_train_rows(roots: list[Path], max_samples: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        if root.is_file() and root.suffix == ".jsonl":
            files = [root]
        else:
            files = sorted(root.rglob("clean.jsonl")) or sorted(root.rglob("train.jsonl"))
        for file in files:
            for row in _iter_jsonl(file):
                rows.append({"messages": record_to_messages(row), "meta": {"source": str(file)}})
                if max_samples is not None and len(rows) >= max_samples:
                    return rows
    return rows


def write_sft_jsonl(rows: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out
