from lebanese_franco_factory.core.config import load_dataset_config


def test_load_conversion_config() -> None:
    cfg = load_dataset_config("arabic_to_franco", {"size": 10})
    assert cfg["family"] == "conversion"
    assert cfg["direction"] == "arabic_to_franco"
    assert cfg["size"] == 10


def test_load_chat_config() -> None:
    cfg = load_dataset_config("chat_sft")
    assert cfg["family"] == "chat_sft"
    assert "greetings" in cfg.get("dictionary_packs", [])


def test_load_spelling_and_instruction() -> None:
    s = load_dataset_config("typos", {"size": 5})
    assert s["family"] == "spelling"
    i = load_dataset_config("explain", {"size": 5})
    assert i["family"] == "instruction"
