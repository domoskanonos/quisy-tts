"""Voice schemas for CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field

SUPPORTED_LANGUAGES = [
    "german",
    "english",
    "french",
    "spanish",
    "italian",
    "portuguese",
    "russian",
    "japanese",
    "korean",
    "chinese",
]


class VoiceCreate(BaseModel):
    """Request schema for creating a new voice."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the voice.",
        json_schema_extra={"example": "Podcast-Sprecher"},
    )
    example_text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Example sentence for this voice.",
        json_schema_extra={"example": "Hallo, ich bin eine künstliche Stimme."},
    )
    instruct: str | None = Field(
        default=None,
        max_length=500,
        description="Instruct text describing the voice style for Qwen TTS.",
        json_schema_extra={"example": "A calm, professional male voice with a warm tone."},
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=2000,
        description="System prompt describing the voice's personality for LLM-driven text generation.",
        json_schema_extra={
            "example": "You are a warm, witty podcast host. Speak conversationally and ask engaging questions."
        },
    )
    language: str = Field(
        default="german",
        description="Language of the voice (e.g. german, english).",
        json_schema_extra={"example": "german"},
    )


class VoiceUpdate(BaseModel):
    """Request schema for updating a voice."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New name for the voice.",
    )
    example_text: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="New example sentence.",
    )
    instruct: str | None = Field(
        default=None,
        max_length=500,
        description="New instruct text for voice style.",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=2000,
        description="System prompt to update the voice's personality.",
    )
    language: str | None = Field(
        default=None,
        description="New language for the voice.",
    )


class VoiceResponse(BaseModel):
    """Response schema for a single voice."""

    id: str
    name: str
    example_text: str
    instruct: str | None = None
    system_prompt: str | None = None
    language: str = "german"
    audio_filename: str | None = None
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


class VoiceListResponse(BaseModel):
    """Response schema for a list of voices."""

    voices: list[VoiceResponse]
    total: int
