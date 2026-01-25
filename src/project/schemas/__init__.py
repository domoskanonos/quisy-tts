"""Request and response schemas for Cosmo TTS API."""

from project.schemas.internal import TTSParams
from project.schemas.languages import LANGUAGE_MAP, resolve_language
from project.schemas.requests import (
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
