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

    voice_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The ID of the voice.",
        json_schema_extra={"example": "podcast-speaker"},
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Example sentence for this voice.",
        json_schema_extra={"example": "Hallo, ich bin eine künstliche Stimme."},
    )
    instruct: str = Field(
        ...,
        max_length=500,
        description="Instruct text describing the voice style for Qwen TTS.",
        json_schema_extra={"example": "A calm, professional male voice with a warm tone."},
    )
    language: str = Field(
        default="de",
        description="Language of the voice (e.g. de).",
        json_schema_extra={"example": "de"},
    )


class VoiceResponse(BaseModel):
    """Response schema for a single voice."""

    voice_id: str
    name: str
    example_text: str
    instruct: str | None = None
    # system_prompt removed: not needed for the TTS-only workflow
    language: str = "german"
    created_at: datetime
    updated_at: datetime


class VoiceListResponse(BaseModel):
    """Response schema for a list of voices."""

    voices: list[VoiceResponse]
    total: int
