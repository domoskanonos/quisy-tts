"""Voice schemas for CRUD operations."""

from datetime import datetime

from pydantic import BaseModel, Field


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


class VoiceResponse(BaseModel):
    """Response schema for a single voice."""

    id: str
    name: str
    example_text: str
    audio_filename: str | None = None
    created_at: datetime
    updated_at: datetime


class VoiceListResponse(BaseModel):
    """Response schema for a list of voices."""

    voices: list[VoiceResponse]
    total: int
