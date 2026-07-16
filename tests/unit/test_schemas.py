import pytest
from pydantic import ValidationError

from lebanese_franco_factory.core.schemas import (
    ChatSFTRecord,
    ConversionRecord,
    InstructionRecord,
    SpellingRecord,
)


def test_conversion_schema_ok() -> None:
    ConversionRecord(
        id="x",
        direction="arabic_to_franco",
        source="كيفك؟",
        target="kifak?",
    )


def test_chat_schema_requires_messages() -> None:
    with pytest.raises(ValidationError):
        ChatSFTRecord(id="x", domain="casual_chat", messages=[])  # type: ignore[arg-type]


def test_spelling_and_instruction_schemas() -> None:
    SpellingRecord(id="s", kind="typos", source="keefak", target="kifak")
    InstructionRecord(
        id="i",
        task="explain",
        instruction="sharhili",
        input="كيفك؟",
        output="kifak? ya3ne how are you",
    )
