"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the Factory repository root (contains pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate repository root")


def dictionary_dir() -> Path:
    return repo_root() / "dictionary"


def rules_dir() -> Path:
    return repo_root() / "data" / "rules"


def plugins_dir() -> Path:
    return repo_root() / "plugins"


def output_dir() -> Path:
    return repo_root() / "output"
