"""Request schemas for Cosmo TTS API."""

from pydantic import BaseModel, Field

from config import ProjectSettings

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
        default_factory=lambda: ProjectSettings().DEFAULT_VOICE_ID,
        description=(
            "Voice ID to use as reference (e.g. 'default_001')."
            " Explicit filenames (e.g. 'chatbot_male.wav') are no longer accepted"
            " — the API accepts only voice IDs which are resolved against the"
            " internal SQLite voices table. If unset, the system will fall back to"
            " the configured DEFAULT_VOICE_ID or the first available voice audio."
        ),
        json_schema_extra={"example": "default_001"},
    )
    ref_text: str | None = Field(
        default=None,
        description=(
            "Transcript of reference audio. Leave empty for faster x_vector_only mode. "
            "Provide text for better quality ICL mode cloning."
        ),
        json_schema_extra={"example": None},
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
    speaker: str = Field(
        ...,
        description="Predefined speaker ID (e.g., 'eric', 'Chelsie').",
        json_schema_extra={"example": "eric"},
    )
    instruct: str | None = Field(
        default=None,
        description="Optional style instruction for the speaker (e.g. 'happy', 'sad').",
        json_schema_extra={"example": ("Sprich wie ein professioneller Podcaster mit tiefer, ruhiger Stimme.")},
    )
