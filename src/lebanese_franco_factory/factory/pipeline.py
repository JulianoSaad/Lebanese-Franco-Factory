"""Generate → validate → clean → export pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lebanese_franco_factory.core.config import load_dataset_config
from lebanese_franco_factory.core.paths import output_dir
from lebanese_franco_factory.core.plugin_loader import load_plugins
from lebanese_franco_factory.factory.cleaner.dedupe import dedupe_records
from lebanese_franco_factory.factory.exporter.jsonl import write_jsonl
from lebanese_franco_factory.factory.exporter.manifests import (
    split_records,
    write_checksums,
    write_dataset_card,
    write_metadata_json,
)
from lebanese_franco_factory.factory.validator.schema_checks import validate_records


def resolve_config(
    dataset: str,
    overrides: dict[str, Any] | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    return load_dataset_config(dataset, overrides=overrides, config_path=config_path)


def run_generate(config: dict[str, Any]) -> Path:
    registry = load_plugins()
    name = config["name"]
    generator_key = name
    if generator_key not in registry.generators:
        # try plugin/family aliases
        for key in (config.get("plugin"), config.get("family"), config.get("direction"), config.get("kind"), config.get("task")):
            if key and key in registry.generators:
                generator_key = key
                break
    if generator_key not in registry.generators:
        available = ", ".join(sorted(registry.generators))
        raise KeyError(f"No generator for {name!r}. Available: {available}")

    records = registry.generators[generator_key](config)
    family = config.get("family", name)
    report = validate_records(records, family=family)
    if report["errors"]:
        raise ValueError(f"Validation failed: {report['errors'][:5]}")

    kept, dropped = dedupe_records(records)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = output_dir() / family / name / stamp
    out.mkdir(parents=True, exist_ok=True)

    write_jsonl(out / "raw.jsonl", records)
    write_jsonl(out / "clean.jsonl", kept)
    if dropped:
        write_jsonl(out / "dropped.jsonl", dropped)

    ratios = (config.get("export") or {}).get("split")
    splits = split_records(kept, ratios=ratios)
    split_paths: list[Path] = []
    for split_name, split_rows in splits.items():
        if not split_rows:
            continue
        path = out / f"{split_name}.jsonl"
        write_jsonl(path, split_rows)
        split_paths.append(path)

    checksums = write_checksums(
        [out / "raw.jsonl", out / "clean.jsonl", *split_paths],
        out / "SHA256SUMS",
    )

    manifest = {
        "dataset": name,
        "family": family,
        "size_raw": len(records),
        "size_clean": len(kept),
        "dropped": len(dropped),
        "seed": config.get("seed"),
        "language": config.get("language"),
        "created_at": stamp,
        "validation": report,
        "checksums": checksums,
        "splits": {k: len(v) for k, v in splits.items()},
        "config": config,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_dataset_card(
        out / "README.md",
        {
            "version": config.get("version", "v0.1"),
            "families": {family: len(kept)},
            "factory_commit": None,
        },
    )
    write_metadata_json(out / "metadata.json", manifest)
    return out


def export_run_to_datasets_repo(
    run_dir: Path,
    datasets_repo: Path,
    version: str = "v0.1",
) -> Path:
    """Copy samples, manifests, checksums into Lebanese-Franco-Datasets layout."""
    target = datasets_repo / version
    target.mkdir(parents=True, exist_ok=True)
    samples = target / "samples"
    manifests = target / "manifests"
    samples.mkdir(exist_ok=True)
    manifests.mkdir(exist_ok=True)

    clean = run_dir / "clean.jsonl"
    if clean.exists():
        lines = clean.read_text(encoding="utf-8").splitlines()
        preview = "\n".join(lines[:50]) + ("\n" if lines else "")
        (samples / f"{run_dir.parent.name}_sample.jsonl").write_text(preview, encoding="utf-8")

    for name in ("manifest.json", "metadata.json", "SHA256SUMS", "README.md"):
        src = run_dir / name
        if src.exists():
            (manifests / f"{run_dir.parent.name}_{name}").write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )

    # refresh top-level metadata aggregate if present
    meta_path = target / "metadata.json"
    existing: dict[str, Any] = {}
    if meta_path.exists():
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
    families = existing.get("families", {})
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    families[manifest["family"]] = families.get(manifest["family"], 0) + manifest["size_clean"]
    existing.update(
        {
            "version": version,
            "status": "generated",
            "families": families,
            "updated_from_run": str(run_dir),
        }
    )
    write_metadata_json(meta_path, existing)
    write_dataset_card(target / "README.md", {"version": version, "families": families})
    return target
