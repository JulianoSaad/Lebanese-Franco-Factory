"""YAML dataset config loader with CLI override merge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.core.schemas import DatasetConfig

# dataset name → relative config path under configs/datasets/
DATASET_CONFIG_MAP: dict[str, str] = {
    "casual_chat": "chat_sft/casual_chat.yaml",
    "chat_sft": "chat_sft/casual_chat.yaml",
    "chat": "chat_sft/casual_chat.yaml",
    "arabic_to_franco": "conversion/arabic_to_franco.yaml",
    "franco_to_arabic": "conversion/franco_to_arabic.yaml",
    "english_to_franco": "conversion/english_to_franco.yaml",
    "franco_to_english": "conversion/franco_to_english.yaml",
    "typos": "spelling/typos.yaml",
    "variants": "spelling/variants.yaml",
    "abbreviations": "spelling/abbreviations.yaml",
    "spelling": "spelling/typos.yaml",
    "explain": "instruction/explain.yaml",
    "summarize": "instruction/summarize.yaml",
    "rewrite": "instruction/rewrite.yaml",
    "instruction": "instruction/explain.yaml",
}


def configs_root() -> Path:
    return repo_root() / "configs" / "datasets"


def load_yaml_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def find_config_path(dataset: str, config_path: str | None = None) -> Path | None:
    if config_path:
        p = Path(config_path)
        return p if p.is_absolute() else repo_root() / p
    rel = DATASET_CONFIG_MAP.get(dataset)
    if not rel:
        # fallback: search by filename stem
        matches = list(configs_root().rglob(f"{dataset}.yaml"))
        return matches[0] if matches else None
    return configs_root() / rel


def load_dataset_config(
    dataset: str,
    overrides: dict[str, Any] | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """Load YAML config for a dataset and merge overrides."""
    path = find_config_path(dataset, config_path=config_path)
    base: dict[str, Any] = {
        "name": dataset,
        "language": "lebanese_franco",
        "size": 100,
        "seed": 42,
        "family": dataset,
    }
    if path and path.exists():
        base.update(load_yaml_config(path))
    else:
        # sensible builtins when YAML missing
        if dataset in {
            "arabic_to_franco",
            "franco_to_arabic",
            "english_to_franco",
            "franco_to_english",
        }:
            base.update({"family": "conversion", "direction": dataset, "plugin": "conversion"})
        elif dataset in {"chat_sft", "casual_chat", "chat"}:
            base.update(
                {
                    "family": "chat_sft",
                    "domain": "casual_chat",
                    "plugin": "chat",
                    "dictionary_packs": ["greetings", "emotions", "verbs"],
                }
            )
        elif dataset in {"typos", "variants", "abbreviations", "spelling"}:
            kind = "typos" if dataset == "spelling" else dataset
            base.update({"family": "spelling", "plugin": "spelling", "kind": kind, "name": kind})
        elif dataset in {"explain", "summarize", "rewrite", "instruction"}:
            task = "explain" if dataset == "instruction" else dataset
            base.update(
                {"family": "instruction", "plugin": "instruction", "task": task, "name": task}
            )

    base["name"] = dataset if dataset in DATASET_CONFIG_MAP else base.get("name", dataset)
    # Keep direction/task/kind aligned with the requested dataset alias
    if dataset in {
        "arabic_to_franco",
        "franco_to_arabic",
        "english_to_franco",
        "franco_to_english",
    }:
        base["name"] = dataset
        base["direction"] = dataset
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})

    # Validate shape (extra fields allowed via model_dump of known fields + passthrough)
    validated = DatasetConfig.model_validate(
        {k: v for k, v in base.items() if k in DatasetConfig.model_fields}
    )
    merged = validated.model_dump()
    # preserve extra keys (kind, task, direction, plugin, etc.)
    for k, v in base.items():
        if k not in merged:
            merged[k] = v
    return merged
