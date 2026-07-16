from lebanese_franco_factory.providers import (
    NotConfiguredProvider,
    Provider,
    available_providers,
    get_provider,
)
from lebanese_franco_factory.providers.ollama import OllamaProvider
from lebanese_franco_factory.providers.openai_provider import OpenAIProvider
from lebanese_franco_factory.providers.vllm_provider import VLLMProvider


def test_provider_registry_lists_backends() -> None:
    names = available_providers()
    for expected in ("ollama", "openai", "litellm", "vllm", "huggingface", "none"):
        assert expected in names


def test_providers_share_abc() -> None:
    assert issubclass(OllamaProvider, Provider)
    assert issubclass(OpenAIProvider, Provider)
    assert issubclass(VLLMProvider, Provider)
    assert isinstance(get_provider("none"), NotConfiguredProvider)


def test_none_provider_raises() -> None:
    p = get_provider("none")
    try:
        p.complete("hi")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass
