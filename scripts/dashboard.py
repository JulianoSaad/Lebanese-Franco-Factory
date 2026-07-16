#!/usr/bin/env python3
"""Thin wrapper → `lff dashboard`."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lebanese_franco_factory.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main(["dashboard", *sys.argv[1:]]))
