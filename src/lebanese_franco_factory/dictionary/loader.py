"""Load modular dictionary packs by name."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lebanese_franco_factory.core.paths import dictionary_dir


class DictionaryError(ValueError):
    """Raised when a dictionary pack is missing or invalid."""


_SKIP_FILES = {"schema.json", "dictionary_index.json"}


def list_packs(base: Path | None = None) -> list[str]:
    root = base or dictionary_dir()
    return sorted(p.stem for p in root.glob("*.json") if p.name not in _SKIP_FILES)


def load_pack(name: str, base: Path | None = None) -> dict[str, Any]:
    root = base or dictionary_dir()
    path = root / f"{name}.json"
    if not path.exists():
        raise DictionaryError(f"Unknown dictionary pack: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("pack") != name:
        raise DictionaryError(f"Pack name mismatch in {path}")
    if "entries" not in data:
        raise DictionaryError(f"Pack missing entries: {path}")
    return data


def load_packs(names: list[str], base: Path | None = None) -> dict[str, dict[str, Any]]:
    return {name: load_pack(name, base=base) for name in names}


def iter_entries(names: list[str], base: Path | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for pack in load_packs(names, base=base).values():
        entries.extend(pack["entries"])
    return entries
