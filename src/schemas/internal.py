"""Internal TTS parameters used by engine."""

from pydantic import BaseModel

from schemas.languages import resolve_language


class TTSParams(BaseModel):
    """Internal parameters for TTS generation."""

    language: str | None = None
    reference_audio: str | None = None
    ref_text: str | None = None
    mode: str = "base"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str = "1.7B"
    ref_audio_path: str | None = None

    @property
    def resolved_language(self) -> str:
        """Returns the full language name, resolving short codes if needed."""
        if not self.language:
            raise ValueError("language is not set on TTSParams")
        return resolve_language(self.language)
