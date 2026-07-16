from lebanese_franco_factory.core.plugin_loader import load_plugins


def test_builtin_plugins_register() -> None:
    registry = load_plugins()
    assert "arabic_to_franco" in registry.generators
    assert "chat_sft" in registry.generators
    assert "conversion" in registry.plugins
    assert "chat" in registry.plugins
