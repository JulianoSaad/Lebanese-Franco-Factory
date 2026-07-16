"""CLI entrypoints for the Factory."""

from __future__ import annotations

import argparse

from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lff-generate", description="Lebanese Franco Factory")
    parser.add_argument("--dataset", required=True, help="Dataset or direction name")
    parser.add_argument("--language", default="lebanese_franco")
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = resolve_config(
        args.dataset,
        {"language": args.language, "size": args.size, "seed": args.seed},
    )
    out = run_generate(config)
    print(f"Wrote {config['size']} examples to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
