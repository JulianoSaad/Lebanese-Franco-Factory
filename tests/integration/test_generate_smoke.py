from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate


def test_generate_arabic_to_franco_smoke() -> None:
    config = resolve_config("arabic_to_franco", {"size": 10, "seed": 1})
    out = run_generate(config)
    assert (out / "raw.jsonl").exists()
    assert (out / "manifest.json").exists()
    lines = (out / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 10


def test_generate_chat_sft_smoke() -> None:
    config = resolve_config("chat_sft", {"size": 5, "seed": 2})
    out = run_generate(config)
    lines = (out / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5
