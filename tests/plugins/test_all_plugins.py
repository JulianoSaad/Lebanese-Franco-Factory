from lebanese_franco_factory.core.plugin_loader import load_plugins
from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate


def test_builtin_plugins_present() -> None:
    reg = load_plugins()
    for name in (
        "chat",
        "conversion",
        "spelling",
        "instruction",
        "augmentation",
        "arabic_to_franco",
        "typos",
        "explain",
    ):
        assert name in reg.generators or name in reg.plugins


def test_each_family_generates_smoke(tmp_path) -> None:
    for dataset in ("casual_chat", "arabic_to_franco", "typos", "explain", "augmentation"):
        cfg = resolve_config(dataset, {"size": 3, "seed": 1})
        out = run_generate(cfg)
        assert (out / "clean.jsonl").exists()
        lines = (out / "clean.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
