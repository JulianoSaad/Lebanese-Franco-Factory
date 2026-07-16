"""Benchmark runner — conversion / chat / slang / typos / reasoning."""

from __future__ import annotations

import json
from typing import Any

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.factory.conversion import convert


def load_bench(name: str) -> list[dict[str, Any]]:
    path = repo_root() / "benchmarks" / name / "golden.json"
    return json.loads(path.read_text(encoding="utf-8"))


def eval_conversion(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or load_bench("conversion")
    ok = 0
    for row in rows:
        got = convert(row["input"], row["direction"])
        if got == row["expected"]:
            ok += 1
    return {"benchmark": "conversion", "n": len(rows), "exact_match": ok / max(len(rows), 1)}


def eval_typos(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or load_bench("typos")
    # rule baseline: target equality when source normalized roughly
    ok = 0
    for row in rows:
        if row["source"].replace("aa", "a").strip() == row["expected"] or row["source"] == row["expected"]:
            ok += 1
        elif row.get("expected") and row["expected"] in row["source"]:
            ok += 1
    return {"benchmark": "typos", "n": len(rows), "heuristic_score": ok / max(len(rows), 1)}


def eval_chat(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or load_bench("chat")
    # structural rubric: non-empty assistant replies present
    ok = sum(1 for r in rows if r.get("assistant"))
    return {"benchmark": "chat", "n": len(rows), "response_present": ok / max(len(rows), 1)}


def eval_slang(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or load_bench("slang")
    ok = sum(1 for r in rows if r.get("franco"))
    return {"benchmark": "slang", "n": len(rows), "coverage": ok / max(len(rows), 1)}


def eval_reasoning(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or load_bench("reasoning")
    ok = sum(1 for r in rows if r.get("answer"))
    return {"benchmark": "reasoning", "n": len(rows), "answered": ok / max(len(rows), 1)}


def run_all() -> dict[str, Any]:
    results = {
        "conversion": eval_conversion(),
        "typos": eval_typos(),
        "chat": eval_chat(),
        "slang": eval_slang(),
        "reasoning": eval_reasoning(),
    }
    out = repo_root() / "output" / "benchmarks" / "latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def main() -> int:
    results = run_all()
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
