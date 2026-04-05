"""Request and response schemas for Cosmo TTS API."""

from .internal import TTSParams
from .languages import LANGUAGE_MAP, resolve_language
from .voice import VoiceCreate, VoiceListResponse, VoiceResponse

__all__ = [
    "LANGUAGE_MAP",
    "resolve_language",
    "TTSParams",
    "VoiceCreate",
    "VoiceResponse",
    "VoiceListResponse",
]
