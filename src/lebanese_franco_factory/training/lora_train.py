"""LoRA training entry — supports --smoke prepare-only without GPU deps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from lebanese_franco_factory.core.paths import repo_root
from lebanese_franco_factory.training.prepare import collect_train_rows, write_sft_jsonl


def load_train_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train LoRA adapter (or smoke-prepare data)")
    parser.add_argument(
        "--config",
        default=str(repo_root() / "configs/training/qwen_lora_default.yaml"),
    )
    parser.add_argument("--smoke", action="store_true", help="Prepare tiny SFT mix only")
    parser.add_argument(
        "--data",
        action="append",
        default=None,
        help="Extra JSONL/run roots (repeatable)",
    )
    args = parser.parse_args(argv)
    cfg = load_train_config(Path(args.config))
    roots = [repo_root() / Path(item["path"]) for item in cfg.get("dataset_mix", [])]
    if args.data:
        roots.extend(Path(p) for p in args.data)

    max_samples = cfg.get("smoke", {}).get("max_samples", 64) if args.smoke else None
    rows = collect_train_rows(roots, max_samples=max_samples)
    out_dir = repo_root() / cfg.get("output_dir", "output/training/run")
    out_dir.mkdir(parents=True, exist_ok=True)
    sft_path = write_sft_jsonl(rows, out_dir / "train_sft.jsonl")
    meta = {
        "model_name_or_path": cfg.get("model_name_or_path"),
        "samples": len(rows),
        "smoke": args.smoke,
        "lora": cfg.get("lora"),
        "train": cfg.get("train"),
        "sft_path": str(sft_path),
    }
    (out_dir / "prepare_manifest.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Prepared {len(rows)} SFT rows at {sft_path}")

    if args.smoke:
        print("Smoke mode: skipping model download/train.")
        return 0

    try:
        from datasets import Dataset  # type: ignore
        from peft import LoraConfig, get_peft_model  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
    except ImportError:
        print(
            "Training dependencies missing. Install extras or re-run with --smoke.\n"
            "pip install transformers datasets peft accelerate torch"
        )
        return 2

    model_id = cfg["model_name_or_path"]
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
    lora_cfg = LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["lora_alpha"],
        lora_dropout=cfg["lora"]["lora_dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    def to_text(example):
        messages = example["messages"]
        text = tokenizer.apply_chat_template(messages, tokenize=False)
        return {"text": text}

    ds = Dataset.from_list(rows).map(to_text)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=cfg["train"].get("max_seq_length", 512),
            padding="max_length",
        )

    tokenized = ds.map(tokenize, batched=True, remove_columns=ds.column_names)
    tokenized = tokenized.map(lambda x: {"labels": x["input_ids"]})

    training_args = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=cfg["train"].get("num_train_epochs", 1),
        per_device_train_batch_size=cfg["train"].get("per_device_train_batch_size", 2),
        learning_rate=float(cfg["train"].get("learning_rate", 2e-4)),
        logging_steps=cfg["train"].get("logging_steps", 10),
        save_steps=cfg["train"].get("save_steps", 200),
        report_to=[],
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    trainer.train()
    model.save_pretrained(out_dir / "adapter")
    tokenizer.save_pretrained(out_dir / "adapter")
    print(f"Saved adapter to {out_dir / 'adapter'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
