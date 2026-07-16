#!/usr/bin/env python3
"""Run Human Review UI on localhost:8081 (dashboard uses 8080)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    import uvicorn

    uvicorn.run(
        "lebanese_franco_factory.review.app:app",
        host="127.0.0.1",
        port=8081,
        reload=False,
    )


if __name__ == "__main__":
    main()
