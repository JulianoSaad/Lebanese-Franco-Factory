"""Read-only helpers that summarise the generated dataset for the web UIs.

The ``output/`` tree holds one dated run-dir per generation (including many
tiny smoke runs). Summing every manifest double-counts those, so we treat the
**largest run per (family, dataset)** as the canonical dataset and report its
size, plus how many runs exist. That yields honest volumes for the browser.
"""

from __future__ import annotations

import json
from pathlib import Path

from lebanese_franco_factory.core.paths import output_dir

FAMILY_LABELS = {
    "chat_sft": "Chat (SFT)",
    "conversion": "Conversion",
    "spelling": "Spelling",
    "instruction": "Instruction",
}
FAMILY_BLURB = {
    "chat_sft": "Multi-turn Lebanese-Franco conversations for supervised fine-tuning.",
    "conversion": "Arabic ↔ Franco ↔ English transliteration pairs.",
    "spelling": "Typo, abbreviation and variant normalisation pairs.",
    "instruction": "Instruction-following tasks (explain / rewrite / summarize).",
}


def _read_manifest(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def dataset_index() -> dict:
    """Group runs by family -> dataset, keeping the biggest run per dataset.

    Returns::

        {family: {"label", "blurb", "size", "runs", "datasets": [
            {"dataset", "size", "runs", "latest_at", "run_dir"}]}}
    """
    out = output_dir()
    # (family, dataset) -> aggregate
    agg: dict[tuple[str, str], dict] = {}
    if out.exists():
        for manifest in out.rglob("manifest.json"):
            data = _read_manifest(manifest)
            if not data:
                continue
            fam = data.get("family")
            ds = data.get("dataset")
            if not fam or not ds:
                continue
            size = int(data.get("size_clean", data.get("size", 0)) or 0)
            created = str(data.get("created_at", "") or "")
            key = (fam, ds)
            cur = agg.setdefault(
                key, {"dataset": ds, "size": 0, "runs": 0, "latest_at": "", "run_dir": ""}
            )
            cur["runs"] += 1
            if created > cur["latest_at"]:
                cur["latest_at"] = created
            if size >= cur["size"]:
                cur["size"] = size
                cur["run_dir"] = str(manifest.parent.relative_to(out))

    families: dict[str, dict] = {}
    for (fam, _ds), info in agg.items():
        f = families.setdefault(
            fam,
            {
                "label": FAMILY_LABELS.get(fam, fam.title()),
                "blurb": FAMILY_BLURB.get(fam, ""),
                "size": 0,
                "runs": 0,
                "datasets": [],
            },
        )
        f["datasets"].append(info)
        f["size"] += info["size"]
        f["runs"] += info["runs"]
    for f in families.values():
        f["datasets"].sort(key=lambda d: -d["size"])
    return dict(sorted(families.items(), key=lambda kv: -kv[1]["size"]))


def totals() -> dict:
    """Headline numbers derived from :func:`dataset_index`."""
    idx = dataset_index()
    return {
        "examples": sum(f["size"] for f in idx.values()),
        "families": len(idx),
        "datasets": sum(len(f["datasets"]) for f in idx.values()),
        "runs": sum(f["runs"] for f in idx.values()),
    }


def display_pair(row: dict) -> dict:
    """Normalise a data row to {left, right, label} for tabular display."""
    fam = row.get("family")
    if fam == "conversion":
        return {"left": row.get("source", ""), "right": row.get("target", ""),
                "label": row.get("direction", "conversion")}
    if fam == "spelling":
        return {"left": row.get("source", ""), "right": row.get("target", ""),
                "label": row.get("kind", "spelling")}
    if fam == "instruction":
        instr = row.get("instruction", "")
        inp = row.get("input", "")
        left = f"{instr} {inp}".strip()
        return {"left": left, "right": row.get("output", ""), "label": row.get("task", "instruction")}
    if fam == "chat_sft":
        msgs = row.get("messages") or []
        left = msgs[0].get("content", "") if len(msgs) > 0 else ""
        right = msgs[1].get("content", "") if len(msgs) > 1 else ""
        return {"left": left, "right": right, "label": row.get("domain", "chat")}
    # generic fallback
    return {"left": str(row.get("source", "")), "right": str(row.get("target", "")),
            "label": str(fam or "")}


def browse_rows(family: str, dataset: str, limit: int = 100) -> tuple[list[dict], dict | None]:
    """Return up to ``limit`` display rows from the biggest run of a dataset."""
    idx = dataset_index()
    fam = idx.get(family)
    if not fam:
        return [], None
    match = next((d for d in fam["datasets"] if d["dataset"] == dataset), None)
    if not match or not match["run_dir"]:
        return [], match
    clean = output_dir() / match["run_dir"] / "clean.jsonl"
    if not clean.exists():
        return [], match
    rows: list[dict] = []
    for line in clean.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(display_pair(json.loads(line)))
        except json.JSONDecodeError:
            continue
        if len(rows) >= limit:
            break
    return rows, match
