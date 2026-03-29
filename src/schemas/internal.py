"""Internal TTS parameters used by engine."""

from pydantic import BaseModel

from schemas.languages import resolve_language


class TTSParams(BaseModel):
    """Internal parameters for TTS generation."""

    # The caller (API layer) must provide the language. No default language
    # is set here to avoid implicit language selection inside services.
    language: str
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
