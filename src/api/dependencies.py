"""FastAPI dependencies for dependency injection."""

from functools import lru_cache

from config import ProjectConfig
from core import CacheService, CleanupService, TTSEngine
from engine import QwenTextToSpeech
from services import FileCacheService, FileCleanupService, TTSService

settings = ProjectConfig.get_settings()


@lru_cache
def get_tts_engine() -> TTSEngine:
    """Returns the TTS engine instance (singleton via lru_cache)."""
    return QwenTextToSpeech()


@lru_cache
def get_cache_service() -> CacheService:
    """Returns the cache service instance (singleton)."""
    return FileCacheService(settings.OUTPUT_DIR)


@lru_cache
def get_cleanup_service() -> CleanupService:
    """Returns the cleanup service instance (singleton)."""
    return FileCleanupService()


@lru_cache
def get_tts_service() -> TTSService:
    """Returns the TTS service instance (singleton)."""
    return TTSService(
        engine=get_tts_engine(),
        cache=get_cache_service(),
    )
