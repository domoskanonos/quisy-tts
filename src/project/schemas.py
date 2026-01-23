"""Request and response schemas for Cosmo TTS API."""

from pydantic import BaseModel, Field

from project.config import ProjectSettings


# Map short language codes to full names expected by Qwen TTS
LANGUAGE_MAP: dict[str, str] = {
    "de": "german",
    "en": "english",
    "fr": "french",
    "es": "spanish",
    "it": "italian",
    "pt": "portuguese",
    "ru": "russian",
    "ja": "japanese",
    "ko": "korean",
    "zh": "chinese",
    "auto": "auto",
}


def resolve_language(lang: str) -> str:
    """Resolves a language code to the full name expected by Qwen TTS."""
    return LANGUAGE_MAP.get(lang, lang)


# =============================================================================
# Base Mode Schemas (Voice Cloning)
# =============================================================================


class BaseGenerateRequest(BaseModel):
    """Request for base mode (voice cloning) generation."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": "Hallo, das ist ein Test."},
    )
    language: str = Field(
        default="german",
        description="Language: 'german', 'english', 'french', etc. or short codes 'de', 'en'.",
        json_schema_extra={"example": "german"},
    )
    reference_audio: str | None = Field(
        default_factory=lambda: ProjectSettings().DEFAULT_REFERENCE_AUDIO,
        description="Filename of reference voice in voices/ directory. Uses default if not provided.",
    )
    ref_text: str | None = Field(
        default=None,
        description="Transcript of reference audio for improved cloning quality.",
    )


# =============================================================================
# Voice Design Mode Schemas
# =============================================================================


class VoiceDesignRequest(BaseModel):
    """Request for voice design mode (1.7B only)."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": "Hello, this is a designed voice."},
    )
    language: str = Field(
        default="english",
        description="Language: 'german', 'english', 'french', etc.",
        json_schema_extra={"example": "english"},
    )
    instruct: str = Field(
        ...,
        description="Natural language voice description.",
        json_schema_extra={"example": "a calm, professional female narrator"},
    )


# =============================================================================
# Custom Voice Mode Schemas
# =============================================================================


class CustomVoiceRequest(BaseModel):
    """Request for custom voice mode with predefined speaker IDs."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": "Dies ist ein Test mit Eric."},
    )
    language: str = Field(
        default="german",
        description="Language: 'german', 'english', 'french', etc.",
        json_schema_extra={"example": "german"},
    )
    speaker: str = Field(
        ...,
        description="Predefined speaker ID (e.g., 'eric', 'Chelsie').",
        json_schema_extra={"example": "eric"},
    )
    instruct: str | None = Field(
        default=None,
        description="Optional style instruction for the speaker.",
    )


# =============================================================================
# Internal TTS Parameters (used by engine)
# =============================================================================


class TTSParams(BaseModel):
    """Internal parameters for TTS generation."""

    language: str = "german"
    reference_audio: str | None = None
    ref_text: str | None = None
    mode: str = "base"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str = "1.7B"

    @property
    def resolved_language(self) -> str:
        """Returns the full language name, resolving short codes if needed."""
        return resolve_language(self.language)
