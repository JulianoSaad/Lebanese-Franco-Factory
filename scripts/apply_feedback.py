#!/usr/bin/env python3
"""Apply human review feedback into the phrase lexicon."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lebanese_franco_factory.factory.feedback import apply_feedback_to_lexicon


def main() -> int:
    stats = apply_feedback_to_lexicon()
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
