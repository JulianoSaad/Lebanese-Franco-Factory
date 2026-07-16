from lebanese_franco_factory.factory.cleaner.dedupe import dedupe_records
from lebanese_franco_factory.factory.exporter.manifests import split_records


def test_dedupe_exact() -> None:
    rows = [
        {
            "id": "1",
            "family": "conversion",
            "direction": "arabic_to_franco",
            "source": "كيفك؟",
            "target": "kifak?",
        },
        {
            "id": "2",
            "family": "conversion",
            "direction": "arabic_to_franco",
            "source": "كيفك؟",
            "target": "kifak?",
        },
    ]
    kept, dropped = dedupe_records(rows)
    assert len(kept) == 1
    assert len(dropped) == 1


def test_split_records() -> None:
    rows = [{"id": str(i)} for i in range(200)]
    splits = split_records(rows)
    assert len(splits["train"]) + len(splits["validation"]) + len(splits["test"]) == 200
