"""Core package - Domain layer (Ports in Hexagonal Architecture)."""

from core.exceptions import (
    AudioGenerationError,
    EngineUnavailableError,
    InvalidLanguageError,
    ReferenceAudioNotFoundError,
    TTSError,
)
from core.interfaces import CacheService, CleanupService, TTSEngine


__all__ = [
    # Interfaces
    "TTSEngine",
    "CacheService",
    "CleanupService",
    # Exceptions
    "TTSError",
    "EngineUnavailableError",
    "InvalidLanguageError",
    "AudioGenerationError",
    "ReferenceAudioNotFoundError",
]
