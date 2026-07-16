"""Generate → validate → export pipeline (cleaner hooks later)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lebanese_franco_factory.core.paths import output_dir
from lebanese_franco_factory.core.plugin_loader import load_plugins
from lebanese_franco_factory.factory.exporter.jsonl import write_jsonl
from lebanese_franco_factory.factory.validator.schema_checks import validate_records


def resolve_config(dataset: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a runtime config from dataset name + CLI overrides."""
    config: dict[str, Any] = {
        "name": dataset,
        "language": "lebanese_franco",
        "size": 100,
        "seed": 42,
    }
    if dataset in {
        "arabic_to_franco",
        "franco_to_arabic",
        "english_to_franco",
        "franco_to_english",
    }:
        config["family"] = "conversion"
        config["direction"] = dataset
        config["plugin"] = "conversion"
    elif dataset in {"chat_sft", "casual_chat", "chat"}:
        config["family"] = "chat_sft"
        config["domain"] = "casual_chat"
        config["plugin"] = "chat"
        config["dictionary_packs"] = ["greetings", "emotions", "verbs"]
    else:
        config["family"] = dataset
    if overrides:
        config.update({k: v for k, v in overrides.items() if v is not None})
    return config


def run_generate(config: dict[str, Any]) -> Path:
    registry = load_plugins()
    name = config["name"]
    if name not in registry.generators:
        available = ", ".join(sorted(registry.generators))
        raise KeyError(f"No generator for {name!r}. Available: {available}")

    records = registry.generators[name](config)
    report = validate_records(records, family=config.get("family", name))
    if report["errors"]:
        raise ValueError(f"Validation failed: {report['errors'][:5]}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = output_dir() / config.get("family", name) / name / stamp
    out.mkdir(parents=True, exist_ok=True)
    raw_path = out / "raw.jsonl"
    write_jsonl(raw_path, records)

    manifest = {
        "dataset": name,
        "family": config.get("family"),
        "size": len(records),
        "seed": config.get("seed"),
        "language": config.get("language"),
        "created_at": stamp,
        "validation": report,
        "config": config,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return out
