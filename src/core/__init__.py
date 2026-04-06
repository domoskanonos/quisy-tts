"""Core package - Domain layer (Ports in Hexagonal Architecture)."""

from core.exceptions import (
    AudioGenerationError,
    EngineUnavailableError,
    InvalidLanguageError,
    ReferenceAudioNotFoundError,
    TTSError,
)
from core.interfaces import CacheService, CleanupService, TTSEngineInterface, TTSServiceInterface, VoiceServiceInterface


__all__ = [
    # Interfaces
    "TTSEngineInterface",
    "CacheService",
    "CleanupService",
    "TTSServiceInterface",
    "VoiceServiceInterface",
    # Exceptions
    "TTSError",
    "EngineUnavailableError",
    "InvalidLanguageError",
    "AudioGenerationError",
    "ReferenceAudioNotFoundError",
]
