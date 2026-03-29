"""FastAPI dependencies for dependency injection."""

from config import ProjectConfig
from core import CacheService, CleanupService, TTSEngine
from engine import QwenTextToSpeech
from services import FileCacheService, FileCleanupService, TTSService, VoiceService


def get_tts_engine() -> TTSEngine:
    """Returns the TTS engine instance."""
    return QwenTextToSpeech()


def get_cache_service() -> CacheService:
    """Returns the cache service instance."""
    return FileCacheService(ProjectConfig.get_settings().AUDIO_DIR)


def get_cleanup_service() -> CleanupService:
    """Returns the cleanup service instance."""
    return FileCleanupService()


def get_tts_service() -> TTSService:
    """Returns the TTS service instance."""
    return TTSService(
        engine=get_tts_engine(),
        cache=get_cache_service(),
    )


def get_voice_service() -> VoiceService:
    """Returns the voice service instance."""
    return VoiceService()
