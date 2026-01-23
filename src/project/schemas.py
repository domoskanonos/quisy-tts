from pydantic import BaseModel


class TTSParams(BaseModel):
    """Parameters for TTS generation."""

    language_id: str = "de"
    reference_audio: str | None = None
    ref_text: str | None = None
    speed: float = 1.0
    mode: str = "base"  # "base", "voice_design", "custom_voice"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str | None = None  # Override default "1.7B" or "0.6B"


class GenerateRequest(BaseModel):
    """API request model for audio generation."""

    text: str
    language_id: str | None = None
    reference_audio: str | None = None
    ref_text: str | None = None
    mode: str | None = "base"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str | None = None
    stream: bool = False
