"""CLI entrypoints for the Factory."""

from __future__ import annotations

import argparse
from pathlib import Path

from lebanese_franco_factory.factory.pipeline import (
    export_run_to_datasets_repo,
    resolve_config,
    run_generate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lff", description="Lebanese Franco Factory")
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("generate", help="Generate a dataset")
    gen.add_argument("--dataset", required=True)
    gen.add_argument("--language", default=None)
    gen.add_argument("--size", type=int, default=None)
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--config", default=None, help="Optional YAML config path")

    exp = sub.add_parser("export", help="Export a run into Datasets repo layout")
    exp.add_argument("--run", required=True, help="Path to a generate output directory")
    exp.add_argument(
        "--datasets-repo",
        default="/var/opt/Franco/Lebanese-Franco-Datasets",
    )
    exp.add_argument("--version", default="v0.1")

    # backwards-compatible top-level flags (scripts/generate.py)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--language", default="lebanese_franco")
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--config", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        target = export_run_to_datasets_repo(
            Path(args.run),
            Path(args.datasets_repo),
            version=args.version,
        )
        print(f"Exported to {target}")
        return 0

    dataset = args.dataset
    if args.command == "generate":
        dataset = args.dataset
        language = args.language
        size = args.size
        seed = args.seed
        config_path = args.config
    else:
        # flat invoke: python -m ... --dataset X
        if not dataset:
            parser.error("--dataset is required (or use: generate --dataset ...)")
        language = args.language
        size = args.size
        seed = args.seed
        config_path = args.config

    config = resolve_config(
        dataset,
        {"language": language, "size": size, "seed": seed},
        config_path=config_path,
    )
    out = run_generate(config)
    print(f"Wrote {config.get('size')} examples to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
