"""Core package - Domain layer (Ports in Hexagonal Architecture)."""

from quisy_tts.core.exceptions import (
    AudioGenerationError,
    EngineUnavailableError,
    InvalidLanguageError,
    ReferenceAudioNotFoundError,
    TTSError,
)
from quisy_tts.core.interfaces import CacheService, CleanupService, TTSEngine, TTSServiceInterface, VoiceServiceInterface


__all__ = [
    # Interfaces
    "TTSEngine",
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
