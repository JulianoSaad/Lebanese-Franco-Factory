import time

from lebanese_franco_factory.factory.pipeline import resolve_config, run_generate


def test_generate_1k_conversion_under_budget() -> None:
    """Smoke performance gate — should stay fast on CPU for rule-based gen."""
    cfg = resolve_config("arabic_to_franco", {"size": 1000, "seed": 7})
    t0 = time.perf_counter()
    out = run_generate(cfg)
    elapsed = time.perf_counter() - t0
    assert (out / "clean.jsonl").exists()
    # Generous bound for CI runners; catches accidental O(n^2) regressions.
    assert elapsed < 30.0, f"too slow: {elapsed:.2f}s"
