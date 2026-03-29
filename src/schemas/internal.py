"""Internal TTS parameters used by engine."""

from pydantic import BaseModel

from schemas.languages import resolve_language


class TTSParams(BaseModel):
    """Internal parameters for TTS generation."""

    # The caller (API layer) must provide the language. No default language is
    # set here to avoid implicit selection inside services. It may be None when
    # TTSParams is used as a transient template, but callers must validate
    # presence before generation.
    language: str | None = None
    reference_audio: str | None = None
    ref_text: str | None = None
    mode: str = "base"
    instruct: str | None = None
    speaker: str | None = None
    model_size: str = "1.7B"

    def model_copy(self) -> "TTSParams":
        """Return a shallow copy usable for per-chunk overrides."""
        return TTSParams(
            language=self.language,
            reference_audio=self.reference_audio,
            ref_text=self.ref_text,
            mode=self.mode,
            instruct=self.instruct,
            speaker=self.speaker,
            model_size=self.model_size,
        )

    @property
    def resolved_language(self) -> str:
        """Returns the full language name, resolving short codes if needed."""
        if not self.language:
            raise ValueError("language is not set on TTSParams")
        return resolve_language(self.language)
