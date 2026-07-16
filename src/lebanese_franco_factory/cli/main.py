"""Unified CLI: lff generate|export|validate|train|evaluate|dashboard|review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lff",
        description="Lebanese Franco Factory — package CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a dataset")
    gen.add_argument("--dataset", required=True)
    gen.add_argument("--language", default=None)
    gen.add_argument("--size", type=int, default=None)
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--config", default=None)

    exp = sub.add_parser("export", help="Export a run into Datasets repo layout")
    exp.add_argument("--run", required=True)
    exp.add_argument("--datasets-repo", default="/var/opt/Franco/Lebanese-Franco-Datasets")
    exp.add_argument("--version", default="v0.1")

    val = sub.add_parser("validate", help="Validate a JSONL file")
    val.add_argument("--file", required=True)
    val.add_argument("--family", required=True)

    train = sub.add_parser("train", help="Prepare/train LoRA")
    train.add_argument("--config", default=None)
    train.add_argument("--smoke", action="store_true")
    train.add_argument("--data", action="append", default=None)

    sub.add_parser("evaluate", help="Run benchmark suite")
    sub.add_parser("dashboard", help="Start dashboard on :8080")
    sub.add_parser("review", help="Start human review UI on :8081")
    sub.add_parser("docs", help="Regenerate docs/api HTML via pdoc")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Back-compat: `lff --dataset X` → generate
    if argv and not argv[0].startswith("-") and argv[0] not in {
        "generate",
        "export",
        "validate",
        "train",
        "evaluate",
        "dashboard",
        "review",
        "docs",
    }:
        pass
    elif argv and argv[0].startswith("--"):
        argv = ["generate", *argv]

    args = build_parser().parse_args(argv)

    if args.command == "generate":
        from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate

        config = resolve_config(
            args.dataset,
            {"language": args.language, "size": args.size, "seed": args.seed},
            config_path=args.config,
        )
        out = run_generate(config)
        print(f"Wrote {config.get('size')} examples to {out}")
        return 0

    if args.command == "export":
        from lebanese_franco_factory.factory.pipeline import export_run_to_datasets_repo

        target = export_run_to_datasets_repo(
            Path(args.run), Path(args.datasets_repo), version=args.version
        )
        print(f"Exported to {target}")
        return 0

    if args.command == "validate":
        from lebanese_franco_factory.factory.validator.schema_checks import validate_records

        rows = [
            json.loads(line)
            for line in Path(args.file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        report = validate_records(rows, family=args.family)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    if args.command == "train":
        from lebanese_franco_factory.training.lora_train import main as train_main

        train_argv: list[str] = []
        if args.config:
            train_argv += ["--config", args.config]
        if args.smoke:
            train_argv.append("--smoke")
        if args.data:
            for d in args.data:
                train_argv += ["--data", d]
        return train_main(train_argv)

    if args.command == "evaluate":
        from lebanese_franco_factory.benchmarks.runner import main as eval_main

        return eval_main()

    if args.command == "dashboard":
        from lebanese_franco_factory.dashboard.app import main as dash_main

        dash_main()
        return 0

    if args.command == "review":
        import uvicorn

        uvicorn.run(
            "lebanese_franco_factory.review.app:app",
            host="127.0.0.1",
            port=8081,
            reload=False,
        )
        return 0

    if args.command == "docs":
        from lebanese_franco_factory.cli.docs import generate_api_docs

        out = generate_api_docs()
        print(f"API docs written to {out}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
