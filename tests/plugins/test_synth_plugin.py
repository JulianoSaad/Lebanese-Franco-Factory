"""Synth plugin — parsing + generation via a stub provider (no live model)."""

from __future__ import annotations

import importlib.util

from lebanese_franco_factory.core.paths import plugins_dir
from lebanese_franco_factory.factory.validator.schema_checks import validate_records


def _load_synth():
    path = plugins_dir() / "synth" / "plugin.py"
    spec = importlib.util.spec_from_file_location("lff_plugin_synth_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_pairs_handles_fences_and_prose() -> None:
    synth = _load_synth()
    text = (
        "Sure! Here you go:\n```json\n"
        '[{"arabic":"كيفك اليوم","franco":"kifak lyom","english":"how are you today"},'
        '{"arabic":"بدي روح عالبيت","franco":"baddi rou7 3al bét","english":"I want to go home"}]'
        "\n```\nHope that helps."
    )
    pairs = synth.parse_pairs(text)
    assert len(pairs) == 2
    assert pairs[0]["franco"] == "kifak lyom"
    assert all("arabic" in p and "franco" in p for p in pairs)


def test_parse_pairs_skips_non_arabic_and_empty() -> None:
    synth = _load_synth()
    text = (
        '[{"arabic":"hello there","franco":"hi"},'  # no Arabic script -> skip
        '{"arabic":"مرحبا","franco":""},'  # empty franco -> skip
        '{"arabic":"صباح الخير","franco":"saba7 lkheir","english":"good morning"}]'
    )
    pairs = synth.parse_pairs(text)
    assert len(pairs) == 1
    assert pairs[0]["franco"] == "saba7 lkheir"


def test_parse_pairs_jsonl_fallback() -> None:
    synth = _load_synth()
    text = (
        '{"arabic":"شو عملت","franco":"shu 3milt","english":"what did you do"}\n'
        '{"arabic":"يلا نروح","franco":"yalla nrou7","english":"lets go"}'
    )
    assert len(synth.parse_pairs(text)) == 2


class _StubProvider:
    """Returns a fixed batch of valid triples, ignoring the prompt."""

    name = "stub"

    def __init__(self, **_: object) -> None:
        self._i = 0

    def complete(self, prompt: str, **_: object) -> str:
        # unique per call so batches don't dedupe to nothing
        self._i += 1
        i = self._i
        return (
            f'[{{"arabic":"جملة رقم {i} ألف","franco":"jumle ra2m {i} alf","english":"phrase {i}"}},'
            f'{{"arabic":"تانية {i} بيت","franco":"tenye {i} bét","english":"second {i}"}}]'
        )


def test_generate_produces_valid_conversion_rows(monkeypatch) -> None:
    synth = _load_synth()
    # inject the stub in place of the real provider registry
    monkeypatch.setattr(
        "lebanese_franco_factory.providers.registry.get_provider",
        lambda name, **kw: _StubProvider(**kw),
    )
    rows = synth.generate(
        {"direction": "arabic_to_franco", "size": 6, "seed": 1, "batch_size": 2, "provider": "ollama"}
    )
    assert len(rows) == 6
    # schema-valid conversion rows
    report = validate_records(rows, family="conversion")
    assert report["ok"], report["errors"]
    # every row flagged for human review and sourced from synth
    assert all(r["meta"]["needs_human"] and r["meta"]["source"] == "synth" for r in rows)
    # arabic_to_franco: source is Arabic, target is Franco
    assert rows[0]["source"].strip() and rows[0]["target"].strip()
    # ids unique
    assert len({r["id"] for r in rows}) == 6


def test_generate_requires_a_provider() -> None:
    synth = _load_synth()
    try:
        synth.generate({"direction": "arabic_to_franco", "size": 2, "provider": "none"})
    except ValueError as exc:
        assert "provider" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("expected ValueError when provider is 'none'")
