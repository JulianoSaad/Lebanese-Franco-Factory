"""Deterministic quality rules for generated rows — no model, no network.

Why: the 2026-10 audit found 99% of generated rows carried a generator counter inside
the training text ("#1", "(3254)", "[8805]"), 77% of rows were duplicates once those were
stripped, and whole datasets were identity pairs (summarize: "kifak?" -> "kifak?"). Those
are decidable by rule, so they must never reach a human reviewer.

Every check returns a list of issue codes; ``classify`` turns them into one verdict:

    reject    - definitely bad (artifact, identity, wrong script, empty)
    duplicate - already seen in this file / in recorded decisions
    verified  - agrees with the dictionary lexicon
    conflict  - contradicts the lexicon (Arabic known, Franco not an accepted spelling)
    review    - nothing automatic to say: a human (or the round-trip check) decides
"""
from __future__ import annotations

import re
import unicodedata

COUNTER_RE = re.compile(r"#\d+|\[\s*\d+\s*\]|\(\s*\d+\s*\)")
ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿ]")
# Arabizi: latin letters, the digit-letters (2 3 5 6 7 8 9), punctuation, spaces.
FRANCO_ALLOWED_RE = re.compile(r"^[A-Za-z0-9 ,.;:!?'\"()\-_/&%+*@\n]*$")
MIN_CHARS = 2
MAX_CHARS = 400
MAX_LEN_RATIO = 4.0


def strip_counters(text: str) -> str:
    out = COUNTER_RE.sub("", text or "")
    return re.sub(r"\s{2,}", " ", out).strip()


def normalize(text: str) -> str:
    """For duplicate detection: counters removed, NFKC, folded case, collapsed spaces."""
    t = unicodedata.normalize("NFKC", strip_counters(text)).lower()
    t = re.sub(r"[ً-ْـ]", "", t)  # Arabic diacritics/tatweel
    return re.sub(r"\s+", " ", t).strip()


def check_text(source: str, target: str, *, expect_identity: bool = False) -> list[str]:
    """Field-level issues that hold for any family."""
    issues: list[str] = []
    s, t = source or "", target or ""
    if COUNTER_RE.search(s) or COUNTER_RE.search(t):
        issues.append("counter_artifact")
    ns, nt = normalize(s), normalize(t)
    if not ns or not nt:
        issues.append("empty_field")
        return issues
    if len(ns) < MIN_CHARS or len(nt) < MIN_CHARS:
        issues.append("too_short")
    if len(ns) > MAX_CHARS or len(nt) > MAX_CHARS:
        issues.append("too_long")
    if ns == nt and not expect_identity:
        issues.append("identity_pair")
    lo, hi = sorted((len(ns), len(nt)))
    if lo and hi / lo > MAX_LEN_RATIO:
        issues.append("length_ratio")
    return issues


def check_scripts(direction: str, source: str, target: str) -> list[str]:
    """Arabic side must be Arabic script; Franco/English side must not be."""
    issues: list[str] = []
    src_lang, _, tgt_lang = (direction or "").partition("_to_")
    for lang, text, side in ((src_lang, source, "source"), (tgt_lang, target, "target")):
        if not lang or not text:
            continue
        has_arabic = bool(ARABIC_RE.search(text))
        if lang == "arabic" and not has_arabic:
            issues.append(f"{side}_not_arabic")
        if lang in ("franco", "english"):
            if has_arabic:
                issues.append(f"{side}_has_arabic")
            elif not FRANCO_ALLOWED_RE.match(strip_counters(text)):
                issues.append(f"{side}_odd_characters")
    return issues


def lex_key(text: str) -> str:
    """Lexicon comparison ignores punctuation: "kifak?" and "kifak" are the same spelling."""
    return re.sub(r"[^\w\u0600-\u06FF ]+", "", normalize(text)).strip()


def lexicon_verdict(arabic: str, franco: str, lexicon: dict[str, set[str]]) -> str:
    """"verified" | "conflict" | "unknown" against {arabic key: {franco keys}}."""
    known = lexicon.get(lex_key(arabic))
    if not known:
        return "unknown"
    return "verified" if lex_key(franco) in known else "conflict"


def classify(issues: list[str], lex: str = "unknown", *, duplicate: bool = False) -> str:
    hard = {"counter_artifact", "empty_field", "identity_pair", "too_short", "too_long"}
    if any(i in hard or i.endswith(("_not_arabic", "_has_arabic")) for i in issues):
        return "reject"
    if duplicate:
        return "duplicate"
    if lex == "conflict":
        return "conflict"
    if lex == "verified" and not issues:
        return "verified"
    return "review"
