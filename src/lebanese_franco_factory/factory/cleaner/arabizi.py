"""Normalize Lebanese Arabizi (Franco) to the house convention — docs/ARABIZI_CONVENTION.md.

Only the mechanical rules live here: generator debris, spacing, casing, the definite article,
attached prefixes, obvious doublings and a few MSA endings. Word choice and naturalness stay
with a native reviewer; this module exists so nobody argues about spacing again.

``normalize_franco`` returns the corrected text. ``franco_violations`` reports what a text
breaks *without* changing it, so ``lff audit`` can flag rows and this module can fix them.
Every rule is listed in ``RULES`` with the convention section it comes from.
"""
from __future__ import annotations

import re
import unicodedata

COUNTER_RE = re.compile(r"#\d+|\[\s*\d+\s*\]|\(\s*\d+\s*\)")
ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿ]")
PROPER_NOUNS = {
    "beirut", "jounieh", "saida", "sour", "tripoli", "trablous", "zahle", "baabda", "jbeil",
    "achrafieh", "hamra", "verdun", "dbayeh", "zalka", "mazraa", "jnah", "ghoubeiry",
    "mansourieh", "chouf", "adma", "idm", "ogero", "whatsapp", "lebanon", "libnan",
}
# §4 negation, §2 MSA vocabulary we always rewrite, §5 vowel spellings the native reviewer fixed.
WORD_FIXES = {
    "ma7": "mesh", "mich": "mesh", "msh": "mesh", "mech": "mesh",
    "sho": "shou", "shu": "shou",
    "shighl": "sheghel", "jam3a": "jem3a",
    "ayna": "wen", "ayn": "wen", "mata": "emta",
    "wakt": "wa2et", "alwakt": "l wa2et",
}
# §4 prefixes that attach to the next word.
ATTACHING_PREFIXES = ("b", "bl", "mn", "mnl")
# §2 MSA case endings.
MSA_ENDINGS = (("aton", ""), ("atoun", ""), ("oun", ""), ("un", ""))

RULES = (
    ("counter_in_text", "§6.1 no generator counters/ids in the text"),
    ("arabic_in_franco", "§6.2 no Arabic script in a Franco field"),
    ("spacing", "§6.4 single spaces, trimmed"),
    ("casing", "§6.5 lowercase except proper nouns"),
    ("msa_article", "§3 the article is 'l', not 'al'/'el'/glued"),
    ("detached_prefix", "§4 'b'/'mn' attach to the next word"),
    ("word_choice", "§2/§4/§5 fixed spellings (mesh, shou, sheghel, wen, ...)"),
    ("doubled_letter", "§5 no accidental doubling"),
    ("msa_ending", "§2 no MSA case endings"),
)


def strip_counters(text: str) -> str:
    return re.sub(r"\s{2,}", " ", COUNTER_RE.sub("", text or "")).strip()


def _fix_article(token: str) -> str:
    """'al internet' -> 'l internet'; 'alshare3' -> 'l share3'; 'el beit' -> 'l beit'."""
    low = token.lower()
    if low in ("al", "el", "il"):
        return "l"
    for prefix in ("al", "el"):
        if low.startswith(prefix) and len(low) > len(prefix) + 2:
            return "l " + low[len(prefix):]
    return token


def _fix_doubles(token: str) -> str:
    """Collapse a doubled letter only at the start, where it is always a typo (kkifak)."""
    if len(token) > 2 and token[0] == token[1] and token[0].isalpha():
        return token[1:]
    return token


def _strip_msa_ending(token: str) -> str:
    for ending, repl in MSA_ENDINGS:
        if len(token) > len(ending) + 2 and token.endswith(ending):
            return token[: -len(ending)] + repl
    return token


ACRONYMS = {"idm", "ogero", "pbx", "sim", "vpn", "dsl", "adsl", "vdsl", "ont", "tv"}


def _case(token: str) -> str:
    """Lowercase, except proper nouns (capitalised) and acronyms (left upper)."""
    base = token.strip(".,!?;:'\"()")
    low = base.lower()
    if low in ACRONYMS:
        return token.upper()
    return token.capitalize() if low in PROPER_NOUNS else token.lower()


def normalize_franco(text: str) -> str:
    """Apply the mechanical rules of the convention. Word choice is left alone."""
    out = unicodedata.normalize("NFKC", strip_counters(text))
    tokens: list[str] = []
    for raw in out.split():
        tok = _case(raw)
        tok = _fix_article(tok)
        head, sep, tail = tok.partition(" ")  # _fix_article may split a glued article
        parts = [head] + ([tail] if sep else [])
        fixed = []
        for part in parts:
            core = part.strip(".,!?;:'\"()")
            punct = part[len(core):] if core and part.startswith(core) else ""
            core = WORD_FIXES.get(core, core)
            core = _fix_doubles(core)
            core = _strip_msa_ending(core)
            fixed.append(core + punct)
        tokens.extend(f for f in fixed if f)
    # §4: a bare attaching prefix joins the following word (b ser3a -> bser3a), but never the
    # article or a name - "b Jounieh" and "b l beit" keep their space.
    joined: list[str] = []
    for tok in tokens:
        core = tok.strip(".,!?;:'\"()")
        is_name = core.lower() in PROPER_NOUNS or core.lower() in ACRONYMS
        if joined and joined[-1] in ATTACHING_PREFIXES and tok != "l" and not is_name:
            joined[-1] = joined[-1] + tok
        else:
            joined.append(tok)
    return " ".join(joined).strip()


def franco_violations(text: str) -> list[str]:
    """Which convention rules this text breaks, without changing it."""
    issues: list[str] = []
    raw = text or ""
    if COUNTER_RE.search(raw):
        issues.append("counter_in_text")
    if ARABIC_RE.search(raw):
        issues.append("arabic_in_franco")
    if raw != raw.strip() or "  " in raw:
        issues.append("spacing")
    tokens = strip_counters(raw).split()
    for tok in tokens:
        core = tok.strip(".,!?;:'\"()")
        low = core.lower()
        if not core:
            continue
        if core != _case(core):
            issues.append("casing")
        if low in ("al", "el", "il") or (low.startswith(("al", "el")) and len(low) > 4
                                        and _fix_article(low) != low):
            issues.append("msa_article")
        if low in WORD_FIXES:
            issues.append("word_choice")
        if _fix_doubles(low) != low:
            issues.append("doubled_letter")
        if _strip_msa_ending(low) != low:
            issues.append("msa_ending")
    for i, tok in enumerate(tokens[:-1]):
        if tok.lower() in ATTACHING_PREFIXES and tokens[i + 1].lower() != "l":
            issues.append("detached_prefix")
    return sorted(set(issues))
