"""FastAPI dependencies for dependency injection."""

import logging
from functools import lru_cache

from config import ProjectConfig
from core.interfaces import AudioConverter, CacheService, CleanupService, TTSEngineInterface, TTSServiceInterface
from engine import QwenTextToSpeech
from infrastructure.audio_converter import PydubAudioConverter
from infrastructure.cache_service import FileCacheService
from infrastructure.cleanup_service import FileCleanupService
from services.ssml_processor import SSMLProcessor
from services.tts_service import TTSService
from services.voice_audio_integrity import VoiceAudioIntegrityService
from services.voice_audio_service import VoiceAudioService
from services.voice_service import VoiceService


def get_logger() -> logging.Logger:
    return ProjectConfig.get_logger()


def get_settings():
    """Returns the project settings."""
    return ProjectConfig.get_settings()


@lru_cache(maxsize=1)
def get_tts_engine() -> TTSEngineInterface:
    """Returns the TTS engine instance (singleton – avoids model reload per request)."""
    return QwenTextToSpeech(settings=get_settings(), logger=get_logger())


@lru_cache(maxsize=1)
def get_cache_service() -> CacheService:
    """Returns the cache service instance (singleton)."""
    return FileCacheService(get_settings().AUDIO_DIR)


@lru_cache(maxsize=1)
def get_cleanup_service() -> CleanupService:
    """Returns the cleanup service instance (singleton)."""
    return FileCleanupService()


@lru_cache(maxsize=1)
def get_voice_service() -> VoiceService:
    """Returns the voice service instance (singleton)."""
    return VoiceService(get_settings().VOICES_DIR)


@lru_cache(maxsize=1)
def get_ssml_processor() -> SSMLProcessor:
    return SSMLProcessor(get_voice_service())


@lru_cache(maxsize=1)
def get_voice_audio_service() -> VoiceAudioService:
    return VoiceAudioService(get_settings().VOICES_DIR)


@lru_cache(maxsize=1)
def get_voice_audio_integrity() -> VoiceAudioIntegrityService:
    return VoiceAudioIntegrityService(
        get_voice_service(), get_voice_audio_service(), get_tts_engine(), get_cache_service()
    )


@lru_cache(maxsize=1)
def get_audio_converter() -> AudioConverter:
    return PydubAudioConverter()


@lru_cache(maxsize=1)
def get_tts_service() -> TTSServiceInterface:
    """Returns the TTS service instance (singleton – avoids engine re-init per request)."""
    return TTSService(
        engine=get_tts_engine(),
        cache=get_cache_service(),
        voice_service=get_voice_service(),
        ssml_processor=get_ssml_processor(),
        voice_audio_integrity=get_voice_audio_integrity(),
        audio_converter=get_audio_converter(),
        logger=get_logger(),
    )
