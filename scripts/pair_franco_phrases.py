"""Pair mined Lebanese Franco phrases with Arabic (and English) for native review.

The mined phrases are real customer speech, so their Lebanese-ness needs no review. What they
lack is the other side of the pair. A local model proposes the Arabic and English; this script
keeps only what survives mechanical checks and a back-translation, and marks the rest for a
person. Nothing is auto-approved: the Arabic is the model's work, not a native's.

Checks per phrase, cheapest first:
  * skip phrases that still contain a redaction placeholder ([PHONE], [EMAIL], ...)
  * the proposed Arabic must be Arabic script, of sane length, and not echo the Franco
  * back-translate the Arabic to Franco and compare with the original (difflib ratio)
  * optionally ask a second model and compare the two Arabic proposals (--agree-model)

Confidence tiers written to the output: "high" (round-trip >= 0.75, and the second model agrees
when one is used), "medium" (round-trip >= 0.55), "low" otherwise. All rows carry
needs_native_review: true.

Usage (data lives outside the public repos):
    python3 scripts/pair_franco_phrases.py \\
        --in /var/opt/Franco/mined/franco_candidates.jsonl \\
        --out /var/opt/Franco/mined/franco_pairs.jsonl \\
        --host http://10.21.100.51:11434 --limit 150
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ARABIC_RE = re.compile(r"[؀-ۿ]")
PLACEHOLDER_RE = re.compile(r"\[(PHONE|EMAIL|URL|NUMBER|HANDLE)\]")
MIN_WORDS = 2

PAIR_PROMPT = (
    "You convert Lebanese Arabizi (Franco, Lebanese dialect written in Latin letters) into "
    "Arabic script.\n"
    "Rules:\n"
    "- Write the SPOKEN LEBANESE in Arabic letters, not Modern Standard Arabic.\n"
    "- Keep the meaning and the tone exactly; do not add or drop words.\n"
    "- Keep foreign words that Lebanese people use as-is (router, internet, wifi).\n"
    "- Also give a short natural English translation.\n"
    'Reply with JSON only: {"arabic": "...", "english": "..."}\n\n'
    "Franco: {franco}"
)
BACK_PROMPT = (
    "Write this Lebanese Arabic sentence in Latin letters the way Lebanese people text "
    "(Arabizi: 3 for ع, 7 for ح, 2 for the glottal stop).\n"
    "Reply with the Latin text only, nothing else.\n\n"
    "Arabic: {arabic}"
)


def ask(host: str, model: str, prompt: str, *, as_json: bool, timeout: float) -> str:
    body = {"model": model, "prompt": prompt, "stream": False, "keep_alive": -1,
            "options": {"temperature": 0, "num_predict": 200}}
    if as_json:
        body["format"] = "json"
    req = urllib.request.Request(f"{host.rstrip('/')}/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = json.loads(r.read()).get("response", "")
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()


def propose(host: str, model: str, franco: str, timeout: float) -> dict | None:
    raw = ask(host, model, PAIR_PROMPT.replace("{franco}", franco), as_json=True, timeout=timeout)
    try:
        body = raw[raw.index("{"): raw.rindex("}") + 1]
        out = json.loads(body)
    except (ValueError, json.JSONDecodeError):
        return None
    arabic, english = str(out.get("arabic") or "").strip(), str(out.get("english") or "").strip()
    return {"arabic": arabic, "english": english} if arabic else None


def mechanical_issues(franco: str, arabic: str) -> list[str]:
    issues = []
    if not ARABIC_RE.search(arabic):
        issues.append("arabic_not_arabic_script")
    if re.search(r"[A-Za-z]{4,}", arabic):
        issues.append("latin_left_in_arabic")
    ratio = len(arabic) / max(len(franco), 1)
    if not 0.35 <= ratio <= 2.5:
        issues.append("length_mismatch")
    if PLACEHOLDER_RE.search(arabic):
        issues.append("placeholder_in_arabic")
    return issues


def similarity(a: str, b: str) -> float:
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 2)


def tier(round_trip: float, agrees: bool | None) -> str:
    if round_trip >= 0.75 and agrees is not False:
        return "high"
    if round_trip >= 0.55:
        return "medium"
    return "low"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--model", default="tony-qwen3-14b-lora")
    ap.add_argument("--agree-model", default=None,
                    help="second model for agreement; loading another 14B evicts the live one")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=180.0)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.src.read_text(encoding="utf-8").splitlines() if l.strip()]
    todo = []
    stats = Counter(input_rows=len(rows))
    for row in rows:
        franco = (row.get("franco") or "").strip()
        if PLACEHOLDER_RE.search(franco):
            stats["skipped_redacted"] += 1
        elif len(franco.split()) < MIN_WORDS:
            stats["skipped_short"] += 1
        else:
            todo.append(row)
    todo = todo[: args.limit or None]
    print(f"pairing {len(todo)} of {len(rows)} phrases with {args.model}", flush=True)

    out_rows, t0 = [], time.monotonic()
    for i, row in enumerate(todo, 1):
        franco = row["franco"].strip()
        proposed = propose(args.host, args.model, franco, args.timeout)
        if not proposed:
            stats["no_proposal"] += 1
            continue
        issues = mechanical_issues(franco, proposed["arabic"])
        if issues:
            stats["mechanical_reject"] += 1
            continue
        back = ask(args.host, args.model, BACK_PROMPT.replace("{arabic}", proposed["arabic"]),
                   as_json=False, timeout=args.timeout)
        rt = similarity(back.splitlines()[-1] if back else "", franco)
        agrees = None
        if args.agree_model:
            second = propose(args.host, args.agree_model, franco, args.timeout)
            agrees = bool(second) and similarity(second["arabic"], proposed["arabic"]) >= 0.6
        confidence = tier(rt, agrees)
        stats[f"tier_{confidence}"] += 1
        out_rows.append({
            "franco": franco, "arabic": proposed["arabic"], "english": proposed["english"],
            "round_trip": rt, "round_trip_text": back.strip()[:120],
            "second_model_agrees": agrees, "confidence": confidence,
            "seen_in_chats": row.get("count", 1), "source": row.get("source"),
            "proposed_by": args.model, "needs_native_review": True,
        })
        if i % 25 == 0:
            print(f"  {i}/{len(todo)}  ({(time.monotonic() - t0) / i:.1f}s/phrase)", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in sorted(out_rows, key=lambda r: (-r["round_trip"], -r["seen_in_chats"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("stats:", dict(stats))
    print(f"pairs written: {len(out_rows):,} -> {args.out}")
    print("\nbest pairs:")
    for r in sorted(out_rows, key=lambda r: -r["round_trip"])[:8]:
        print(f"  [{r['confidence']:6s} rt={r['round_trip']}] {r['franco'][:46]} | {r['arabic'][:40]} | {r['english'][:34]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
