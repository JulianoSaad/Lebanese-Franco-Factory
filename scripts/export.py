#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lebanese_franco_factory.factory.cli import main

if __name__ == "__main__":
    # normalize to export subcommand
    argv = sys.argv[1:]
    if argv and argv[0] != "export":
        argv = ["export", *argv]
    raise SystemExit(main(argv))
