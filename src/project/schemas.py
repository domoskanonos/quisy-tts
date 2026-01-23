from pydantic import BaseModel, Field


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


class TTSParams(BaseModel):
    """Parameters for TTS generation."""

    language_id: str = "german"
    reference_audio: str | None = None
    ref_text: str | None = None
    speed: float = 1.0
    mode: str = "base"  # "base", "voice_design", "custom_voice"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str | None = None  # Override default "1.7B" or "0.6B"

    @property
    def resolved_language(self) -> str:
        """Returns the full language name, resolving short codes if needed."""
        return LANGUAGE_MAP.get(self.language_id, self.language_id)


class GenerateRequest(BaseModel):
    """API request model for audio generation."""

    text: str = Field(
        ...,
        description="The text to convert to speech.",
        json_schema_extra={"example": "Hallo, das ist ein Test der Sprachausgabe."},
    )
    language_id: str | None = Field(
        default=None,
        description="Language code (e.g., 'de', 'en'). Defaults to server config.",
        json_schema_extra={"example": "de"},
    )
    reference_audio: str | None = Field(
        default=None,
        description="Filename of a reference voice in the voices/ directory.",
    )
    ref_text: str | None = Field(
        default=None,
        description="Transcript of the reference audio for better cloning.",
    )
    mode: str | None = Field(
        default="base",
        description="Generation mode: 'base', 'voice_design', or 'custom_voice'.",
        json_schema_extra={"example": "base"},
    )
    instruct: str | None = Field(
        default=None,
        description="For 'voice_design' mode: natural language voice description.",
        json_schema_extra={"example": "a calm, professional narrator"},
    )
    speaker: str | None = Field(
        default=None,
        description="For 'custom_voice' mode: a predefined speaker ID.",
    )
    model_size: str | None = Field(
        default=None,
        description="Model variant: '1.7B' or '0.6B'. Defaults to server config.",
        json_schema_extra={"example": "0.6B"},
    )
    stream: bool = Field(
        default=False,
        description="If true, returns raw PCM audio chunks. Not playable in Swagger.",
    )
