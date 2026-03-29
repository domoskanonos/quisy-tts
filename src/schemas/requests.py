"""Request schemas for Cosmo TTS API."""

from pydantic import BaseModel, Field

from config import ProjectConfig

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
        default="German",
        description="Language: 'German', 'English', 'French', etc.",
        json_schema_extra={"example": "German"},
    )
    reference_audio: str | None = Field(
        default_factory=lambda: ProjectConfig.get_settings().DEFAULT_VOICE_ID,
        description=(
            "Voice ID to use as reference (e.g. 'default_001')."
            " Explicit filenames (e.g. 'chatbot_male.wav') are no longer accepted"
            " — the API accepts only voice IDs which are resolved against the"
            " internal SQLite voices table. If unset, the system will fall back to"
            " the configured DEFAULT_VOICE_ID or the first available voice audio."
        ),
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
        default="German",
        description="Language: 'German', 'English', 'French', etc.",
        json_schema_extra={"example": "German"},
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
        default="German",
        description="Language: 'German', 'English', 'French', etc.",
        json_schema_extra={"example": "German"},
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
