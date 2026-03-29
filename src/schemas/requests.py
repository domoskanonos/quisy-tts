"""Request schemas for Cosmo TTS API."""

from pydantic import BaseModel, Field

from config import ProjectConfig

# =============================================================================
# Generation Schemas
# =============================================================================


class GenerateRequest(BaseModel):
    """Request for text-to-speech generation."""

    text: str = Field(..., description="The text to convert to speech.")
    language: str = Field(default="de", description="Language code (e.g., 'de', 'en').")
    voice_id: str = Field(..., description="The ID of the voice to use.")


class CreateVoiceRequest(BaseModel):
    """Request for creating a new voice and generating its preview audio."""

    voice_id: str = Field(..., description="The ID for the new voice.")
    instruct: str = Field(..., description="Voice design instruction.")
    language: str = Field(default="de", description="Language code (e.g., 'de', 'en').")
    text: str = Field(..., description="The text to generate the preview audio from.")


# =============================================================================
# Base Mode Schemas (Voice Cloning)
# =============================================================================


class BaseGenerateRequest(BaseModel):
    """Request for base mode (voice cloning) generation."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": "Hallo, ich bin eine künstliche Stimme."},
    )
    language: str = Field(
        default="de",
        description="Language: 'de', 'en', 'fr', etc.",
        json_schema_extra={"example": "de"},
    )
    reference_audio: str = Field(
        ...,
        description="Voice ID to use as reference (e.g. 'default_001').",
        json_schema_extra={"example": "default_001"},
    )


# =============================================================================
# Voice Design Mode Schemas
# =============================================================================


class VoiceDesignRequest(BaseModel):
    """Request for voice design mode (1.7B only)."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": ("Ich freu mich Sie kennen zu lernen. Gerne leihe ich ihnen meine Stimme.")},
    )
    language: str = Field(
        default="de",
        description="Language: 'de', 'en', 'fr', etc.",
        json_schema_extra={"example": "de"},
    )
    instruct: str = Field(
        ...,
        description="Natural language voice description.",
        json_schema_extra={"example": ("Eine tiefe, ruhige männliche Stimme, wie ein professioneller Podcaster.")},
    )


# =============================================================================
# Custom Voice Mode Schemas
# =============================================================================


class CustomVoiceRequest(BaseModel):
    """Request for custom voice mode with predefined speaker IDs."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": ("Ich freu mich Sie kennen zu lernen. Gerne leihe ich ihnen meine Stimme.")},
    )
    language: str = Field(
        default="de",
        description="Language: 'de', 'en', 'fr', etc.",
        json_schema_extra={"example": "de"},
    )
    voice_id: str = Field(
        ...,
        description="Predefined voice ID (use /voices search to find).",
        json_schema_extra={"example": "default_001"},
    )
    instruct: str | None = Field(
        default=None,
        description="Optional style instruction for the speaker (e.g. 'happy', 'sad').",
        json_schema_extra={"example": ("Sprich wie ein professioneller Podcaster mit tiefer, ruhiger Stimme.")},
    )


class ConcatenateAudioRequest(BaseModel):
    """Request for concatenating audio files."""

    audio_files: list[str] = Field(
        ...,
        description="List of filenames of audio files to concatenate.",
        json_schema_extra={"example": ["audio1.wav", "audio2.wav"]},
    )
