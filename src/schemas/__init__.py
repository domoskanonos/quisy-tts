"""Request and response schemas for Cosmo TTS API."""

from schemas.internal import TTSParams
from schemas.languages import LANGUAGE_MAP, resolve_language
from schemas.requests import (
    BaseGenerateRequest,
    CustomVoiceRequest,
    VoiceDesignRequest,
)


__all__ = [
    "LANGUAGE_MAP",
    "resolve_language",
    "BaseGenerateRequest",
    "VoiceDesignRequest",
    "CustomVoiceRequest",
    "TTSParams",
]
