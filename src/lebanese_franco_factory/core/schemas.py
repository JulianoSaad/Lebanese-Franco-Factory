"""Pydantic record schemas for all dataset families."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatSFTRecord(BaseModel):
    id: str
    family: Literal["chat_sft"] = "chat_sft"
    domain: str
    language: str = "lebanese_franco"
    messages: list[ChatMessage] = Field(min_length=2)
    meta: dict[str, Any] = Field(default_factory=dict)


class ConversionRecord(BaseModel):
    id: str
    family: Literal["conversion"] = "conversion"
    direction: str
    source: str
    target: str
    meta: dict[str, Any] = Field(default_factory=dict)


class SpellingRecord(BaseModel):
    id: str
    family: Literal["spelling"] = "spelling"
    kind: Literal["typos", "variants", "abbreviations"]
    source: str
    target: str
    meta: dict[str, Any] = Field(default_factory=dict)


class InstructionRecord(BaseModel):
    id: str
    family: Literal["instruction"] = "instruction"
    task: Literal["explain", "summarize", "rewrite"]
    instruction: str
    input: str
    output: str
    meta: dict[str, Any] = Field(default_factory=dict)


class DatasetConfig(BaseModel):
    name: str
    plugin: str | None = None
    family: str
    language: str = "lebanese_franco"
    version: str = "0.1.0"
    size: int = 100
    seed: int = 42
    domain: str | None = None
    direction: str | None = None
    dictionary_packs: list[str] = Field(default_factory=list)
    variation: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    export: dict[str, Any] = Field(
        default_factory=lambda: {
            "format": "jsonl",
            "split": {"train": 0.98, "validation": 0.01, "test": 0.01},
        }
    )
