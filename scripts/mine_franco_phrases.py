"""Mine genuine Lebanese Franco phrases from real customer chats.

Why: the generated corpus has 392k rows but only ~86k distinct examples, and its conversion
core is ~500 real pairs per direction, because everything derives from a 99-word lexicon.
Real customers already write Lebanese Arabizi every day in the WhatsApp/Chatwoot inboxes;
mining that needs no naturalness review, because it *is* natural.

Privacy: this reads customer messages, so it redacts before anything is written — phone
numbers, emails, URLs, long digit runs (account/IBAN/ID), @mentions — using the same shapes
as the Operation Guide exporter. Output is written outside any git repo; the Lebanese-Franco-*
repos are public and must never receive customer text.

Usage (on the server holding the Chatwoot database):
    python3 franco_mine.py --out /var/opt/Franco/mined/franco_candidates.jsonl [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# --- privacy -------------------------------------------------------------------------------
REDACTIONS = (
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
    (re.compile(r"https?://\S+|www\.\S+"), "[URL]"),
    (re.compile(r"\+?\d[\d\s/-]{6,}\d"), "[PHONE]"),      # 03 123456, +961 ..., 01-650650
    (re.compile(r"\b\d{5,}\b"), "[NUMBER]"),               # account/ID/IBAN-like runs
    (re.compile(r"(?<!\w)@\w+"), "[HANDLE]"),
    # WhatsApp/Chatwoot forward labels carry the sender's name: "*Rita K:* ..." / "~ Rita:"
    (re.compile(r"^\s*[*~]\s*[^*:~\n]{1,40}\s*:?\s*[*~]?\s*"), ""),
)

# Email and ticketing debris that reaches the inbox but is not customer speech.
NOT_SPEECH_RE = re.compile(
    r"^\s*>|betreff|^\s*(aw|re|fw|fwd)\s*:|incident\s+inc|^\s*(from|sent|to|subject|cc)\s*:"
    r"|unsubscribe|no-?reply|ticket\s*#?\d|sdn\.?\s*bhd|gmbh|\bco\.,?\s*ltd\b",
    re.I,
)

# --- what counts as Lebanese Franco --------------------------------------------------------
ARABIC_RE = re.compile(r"[؀-ۿ]")
# Arabizi letter-digits used inside a word: kif2k, 3andi, mn7ebbik, 5alas
ARABIZI_DIGIT_RE = re.compile(r"[a-z][2357890]|[2357890][a-z]", re.I)
LEBANESE_MARKERS = {
    "kifak", "kifik", "kifkom", "shu", "shou", "sho", "bade", "badde", "baddi", "mnih", "mni7",
    "yalla", "yala", "halla", "halla2", "hala2", "lkan", "ma", "mesh", "mish", "mech", "msh",
    "fi", "fii", "ma3", "ma3ak", "ma3ik", "3andi", "3andak", "3ande", "3a", "la", "la2", "eh",
    "aywa", "tayeb", "tayyeb", "khalas", "5alas", "tfaddal", "tfadal", "btefham", "fhemet",
    "bi2oul", "bados", "lazem", "lezem", "mnne7", "ktir", "kteer", "shway", "shwaye", "hek",
    "heik", "haydaa", "hayda", "hayde", "balash", "bala", "ba3den", "ba3dein", "iza", "izza",
    "sa7", "sa77", "akid", "akeed", "wallah", "wallaw", "ya3ne", "ya3ni", "khayye", "habibi",
    "7abibi", "7abibe", "mabrouk", "inshallah", "nshallah", "7amdella", "7amdelle", "sabah",
    "masa", "marhaba", "mar7aba", "merci", "merce", "bonjour", "bonjourein", "ok", "okey",
    "rje3", "rja3", "ba3at", "ba3atlak", "3atini", "a3tini", "jebli", "jibli", "khod", "khid",
    "rou7", "rou7e", "nrou7", "ta3", "ta3i", "ejri", "sar", "sarr", "shaghel", "sheghel",
    "bayt", "beit", "l", "el", "w", "wl", "aw", "law", "min", "mn", "3al", "3ala", "kell",
    "kol", "kil", "ba3ref", "ba3rif", "b3ref", "fahem", "fehem", "ta3banet", "ta3ban",
}
MIN_WORDS, MAX_WORDS, MIN_CHARS = 2, 25, 6


def redact(text: str) -> str:
    out = text or ""
    for pattern, repl in REDACTIONS:
        out = pattern.sub(repl, out)
    return re.sub(r"\s+", " ", out).strip()


def looks_franco(text: str) -> bool:
    """Latin-script Lebanese: Arabizi digits, or enough Lebanese marker words."""
    if ARABIC_RE.search(text) or NOT_SPEECH_RE.search(text):
        return False                       # Arabic script or email/ticket debris
    letters = sum(c.isalpha() for c in text)
    if letters < MIN_CHARS or not (MIN_WORDS <= len(text.split()) <= MAX_WORDS):
        return False
    if text.count("[") > 1:                # mostly redacted placeholders
        return False
    words = [w.strip(".,!?;:()'\"").lower() for w in text.split()]
    markers = sum(1 for w in words if w in LEBANESE_MARKERS)
    if ARABIZI_DIGIT_RE.search(text) and markers >= 1:
        return True
    # marker-only evidence needs a real sentence, not "ok merci"
    return len(words) >= 3 and markers >= 2 and markers / len(words) >= 0.25


def fetch_stdin() -> list[str]:
    """One message per line on stdin - for any other source (website chat logs, exports)."""
    return [l.rstrip("\n") for l in sys.stdin]


def fetch_messages(limit: int | None) -> list[str]:
    """Incoming (customer) messages from the Chatwoot database, newest first."""
    sql = ("select content from messages where message_type = 0 and content is not null "
           "and content <> '' order by id desc")
    if limit:
        sql += f" limit {int(limit)}"
    out = subprocess.run(
        ["docker", "exec", "chatwoot-chatwoot-postgres-1", "psql", "-U", "chatwoot",
         "-d", "chatwoot", "-At", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.splitlines()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--source", choices=("chatwoot", "stdin"), default="chatwoot",
                    help="chatwoot: read the Chatwoot DB here; stdin: one message per line")
    ap.add_argument("--label", default=None, help="source label stored on each row")
    args = ap.parse_args()

    raw = fetch_stdin() if args.source == "stdin" else fetch_messages(args.limit)
    label = args.label or f"{args.source}-incoming"
    stats = Counter(total=len(raw))
    seen: dict[str, dict] = {}
    arabic: dict[str, dict] = {}
    for line in raw:
        text = redact(line)
        if not text:
            stats["empty_after_redaction"] += 1
            continue
        if ARABIC_RE.search(text):
            stats["arabic_script"] += 1
            if not NOT_SPEECH_RE.search(text) and 2 <= len(text.split()) <= MAX_WORDS:
                key = re.sub(r"\s+", " ", text).strip(" .!?؟")
                arabic.setdefault(key, {"arabic": key, "count": 0, "source": label})
                arabic[key]["count"] += 1
            continue
        if not looks_franco(text):
            stats["not_franco"] += 1
            continue
        key = re.sub(r"\s+", " ", text.lower()).strip(" .!?")
        if key in seen:
            seen[key]["count"] += 1
            stats["duplicate"] += 1
            continue
        seen[key] = {"franco": text, "count": 1, "source": label}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in sorted(seen.values(), key=lambda r: -r["count"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    ar_out = args.out.with_name(args.out.stem + "_arabic.jsonl")
    with ar_out.open("w", encoding="utf-8") as f:
        for row in sorted(arabic.values(), key=lambda r: -r["count"]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("scanned:", dict(stats))
    print(f"distinct Franco phrases: {len(seen):,} -> {args.out}")
    print(f"distinct Arabic-script phrases: {len(arabic):,} -> {ar_out}")
    print("\nmost repeated (redacted):")
    for row in sorted(seen.values(), key=lambda r: -r["count"])[: args.samples]:
        print(f"  x{row['count']:<4} {row['franco'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
