"""Run the quality rules over a JSONL file or a run dir, and report what needs a human.

    lff validate data/review/needs_human_v0.2.jsonl
    lff validate output/conversion/arabic_to_franco/<run> --round-trip

``--round-trip`` is the one optional model step: for Arabic->Franco rows the Franco is
translated back to Arabic by the configured provider (Tony by default) and compared to the
original. Agreement is strong evidence the row is right; it only runs for rows the rules
left as "review", so it never spends model time on rows already decided.
"""
from __future__ import annotations

import difflib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.factory.validator.quality import (
    classify,
    lex_key,
    lexicon_verdict,
    normalize,
    check_scripts,
    check_text,
)

IDENTITY_OK = {"variants", "summarize"}  # datasets where input == output is legitimate
# Back-translation rarely reproduces the source verbatim (معاك vs معك), so compare with a
# similarity ratio instead of equality. Calibrated against the recorded human decisions.
ROUND_TRIP_MATCH = 0.80
ROUND_TRIP_PARTIAL = 0.60

JUDGE_PROMPT = (
    "You check Lebanese Arabizi (Franco) data. Given the Arabic and the Franco writing of it, answer:\n"
    "1. same_meaning: does the Franco say the same thing as the Arabic?\n"
    "2. natural_lebanese: would a Lebanese person actually text it that way (Lebanese dialect, not "
    "Modern Standard Arabic transliteration, no invented spellings)?\n"
    'Reply with JSON only: {"same_meaning": true/false, "natural_lebanese": true/false, "fix": "<better '
    'Franco spelling or empty>"}\n\nArabic: {arabic}\nFranco: {franco}'
)


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def load_lexicon(dictionary_dir: Path | None = None) -> dict[str, set[str]]:
    """{normalized arabic: {normalized franco spellings}} from the dictionary packs."""
    root = dictionary_dir or (repo_root() / "dictionary")
    lex: dict[str, set[str]] = {}
    for path in sorted(root.glob("*.json")):
        try:
            pack = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in pack.get("entries") or []:
            ar = lex_key(entry.get("arabic", ""))
            if not ar:
                continue
            spellings = entry.get("franco")
            spellings = [spellings] if isinstance(spellings, str) else (spellings or [])
            lex.setdefault(ar, set()).update(lex_key(s) for s in spellings if s)
    return lex


def row_fields(rec: dict) -> tuple[str, str, str, str]:
    """(direction, dataset, source, target) for conversion/spelling/instruction rows."""
    meta = rec.get("meta") or {}
    direction = rec.get("direction") or meta.get("direction") or ""
    dataset = rec.get("kind") or rec.get("task") or rec.get("domain") or direction
    if "messages" in rec:
        msgs = rec["messages"]
        src = " | ".join(m.get("content", "") for m in msgs if m.get("role") == "user")
        tgt = " | ".join(m.get("content", "") for m in msgs if m.get("role") == "assistant")
        return direction, dataset or "chat", src, tgt
    src = rec.get("source") or rec.get("input") or meta.get("arabic") or ""
    tgt = rec.get("target") or rec.get("output") or meta.get("franco") or ""
    return direction, dataset, str(src), str(tgt)


def validate_rows(rows: Iterable[dict], lexicon: dict[str, set[str]],
                  seen: set[tuple[str, str]] | None = None) -> list[dict]:
    seen = seen if seen is not None else set()
    out: list[dict] = []
    for rec in rows:
        direction, dataset, src, tgt = row_fields(rec)
        issues = check_text(src, tgt, expect_identity=dataset in IDENTITY_OK)
        issues += check_scripts(direction, src, tgt)
        key = (normalize(src), normalize(tgt))
        duplicate = key in seen
        seen.add(key)
        lex = "unknown"
        if "arabic" in (direction or "") or (rec.get("meta") or {}).get("arabic"):
            ar = src if direction.startswith("arabic") else ((rec.get("meta") or {}).get("arabic") or "")
            fr = tgt if direction.startswith("arabic") else src
            if ar and fr:
                lex = lexicon_verdict(ar, fr, lexicon)
        out.append({
            "id": rec.get("id"),
            "dataset": dataset or direction or "?",
            "source": src,
            "target": tgt,
            "issues": issues,
            "lexicon": lex,
            "verdict": classify(issues, lex, duplicate=duplicate),
        })
    return out


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def round_trip(results: list[dict], *, provider_name: str = "ollama", model: str = "tony-qwen3-14b-lora",
               host: str = "http://127.0.0.1:11434", limit: int | None = None, timeout: float = 120.0) -> dict:
    """Back-translate Franco -> Arabic for rows left as 'review'; compare to the source."""
    from lebanese_franco_factory.providers.registry import get_provider

    kwargs = {"model": model, "timeout": timeout}
    if provider_name == "ollama":
        kwargs["host"] = host
    provider = get_provider(provider_name, **kwargs)
    todo = [r for r in results if r["verdict"] == "review"][: limit or None]
    counts = Counter()
    for r in todo:
        prompt = ("Translate this Lebanese Arabizi (Franco) text into Arabic script. "
                  "Reply with the Arabic only, no explanation.\n\n" + r["target"])
        try:
            back = provider.complete(prompt, model=model, timeout=timeout)
        except Exception as exc:  # provider down: leave the row for a human
            r["round_trip"] = f"error: {exc}"
            counts["error"] += 1
            continue
        got, want = normalize(back.splitlines()[-1] if back else ""), normalize(r["source"])
        score = similarity(got, want) if got else 0.0
        r["round_trip_score"] = round(score, 2)
        if score >= ROUND_TRIP_MATCH:
            r["round_trip"], r["verdict"] = "match", "verified"
            counts["match"] += 1
        elif score >= ROUND_TRIP_PARTIAL:
            r["round_trip"] = f"partial ({score:.2f}): {got[:40]}"
            counts["partial"] += 1
        else:
            r["round_trip"] = f"differs ({score:.2f}): {got[:40]}"
            counts["differs"] += 1
    return dict(counts)


def judge(results: list[dict], *, provider_name: str = "ollama", model: str = "tony-qwen3-14b-lora",
          host: str = "http://127.0.0.1:11434", limit: int | None = None, timeout: float = 120.0,
          only: tuple[str, ...] = ("review",)) -> dict:
    """Ask a model whether each row means the same AND reads as natural Lebanese."""
    from lebanese_franco_factory.providers.registry import get_provider

    kwargs = {"model": model, "timeout": timeout}
    if provider_name == "ollama":
        kwargs["host"] = host
    provider = get_provider(provider_name, **kwargs)
    todo = [r for r in results if r["verdict"] in only][: limit or None]
    counts = Counter()
    for r in todo:
        prompt = JUDGE_PROMPT.replace("{arabic}", r["source"]).replace("{franco}", r["target"])
        try:
            raw = provider.complete(prompt, model=model, timeout=timeout, format="json")
        except Exception as exc:
            r["judge"] = f"error: {exc}"
            counts["error"] += 1
            continue
        try:
            body = raw[raw.index("{"): raw.rindex("}") + 1]
            out = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            r["judge"] = "unparsed"
            counts["unparsed"] += 1
            continue
        ok = bool(out.get("same_meaning")) and bool(out.get("natural_lebanese"))
        r["judge"] = "ok" if ok else "flag"
        r["judge_detail"] = out
        if not ok:
            r["verdict"] = "judge_flag"
        counts["ok" if ok else "flag"] += 1
    return dict(counts)


def summarize(results: list[dict]) -> dict:
    by_verdict = Counter(r["verdict"] for r in results)
    issues = Counter(i for r in results for i in r["issues"])
    return {"rows": len(results), "verdicts": dict(by_verdict), "issues": dict(issues)}


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="lff audit", description=__doc__)
    ap.add_argument("path", help="JSONL file or a run directory (uses train.jsonl)")
    ap.add_argument("--round-trip", action="store_true", help="back-translate 'review' rows via a provider")
    ap.add_argument("--judge", action="store_true", help="model-judge meaning + naturalness of 'review' rows")
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="tony-qwen3-14b-lora")
    ap.add_argument("--host", default="http://127.0.0.1:11434", help="ollama host for --round-trip")
    ap.add_argument("--limit", type=int, default=None, help="cap round-trip calls")
    ap.add_argument("--report", type=Path, default=None, help="write per-row results as JSON")
    args = ap.parse_args(argv)

    path = Path(args.path)
    if path.is_dir():
        path = path / "train.jsonl"
    rows = read_jsonl(path)
    results = validate_rows(rows, load_lexicon())
    summary = summarize(results)
    print(f"{path}: {summary['rows']} rows")
    for verdict, n in sorted(summary["verdicts"].items(), key=lambda kv: -kv[1]):
        print(f"  {verdict:10s} {n:6,} ({100 * n / max(summary['rows'], 1):.1f}%)")
    if summary["issues"]:
        print("  issues:", ", ".join(f"{k}={v}" for k, v in sorted(summary["issues"].items(), key=lambda kv: -kv[1])))
    if args.round_trip:
        rt = round_trip(results, provider_name=args.provider, model=args.model, host=args.host,
                        limit=args.limit)
        print(f"  round-trip ({args.model}): {rt}")
        summary = summarize(results)
        print("  after round-trip:", summary["verdicts"])
    if args.judge:
        jg = judge(results, provider_name=args.provider, model=args.model, host=args.host, limit=args.limit)
        print(f"  judge ({args.model}): {jg}")
        summary = summarize(results)
        print("  after judge:", summary["verdicts"])
    needs_human = sum(1 for r in results if r["verdict"] in ("review", "conflict"))
    print(f"  needs a human: {needs_human:,} of {summary['rows']:,} "
          f"({100 * needs_human / max(summary['rows'], 1):.1f}%)")
    if args.report:
        args.report.write_text(json.dumps({"summary": summary, "rows": results}, ensure_ascii=False, indent=1))
        print(f"  report -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
