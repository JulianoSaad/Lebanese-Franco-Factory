from lebanese_franco_factory.dictionary.loader import iter_entries, list_packs, load_pack


def test_list_packs_includes_greetings_and_sports() -> None:
    packs = list_packs()
    assert "greetings" in packs
    assert "sports" in packs
    assert "work" in packs


def test_load_pack_greetings() -> None:
    pack = load_pack("greetings")
    assert pack["pack"] == "greetings"
    assert len(pack["entries"]) >= 5


def test_iter_entries_selected_packs() -> None:
    entries = iter_entries(["sports", "technology"])
    tags = {t for e in entries for t in e.get("tags", [])}
    assert "sports" in tags
    assert "technology" in tags
