#!/usr/bin/env python3
"""Validate a JSONL file against family schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lebanese_franco_factory.factory.validator.schema_checks import validate_records


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--family", required=True)
    args = p.parse_args()
    rows = [
        json.loads(line)
        for line in Path(args.file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = validate_records(rows, family=args.family)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
