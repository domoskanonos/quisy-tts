"""FastAPI dependencies for dependency injection."""

import logging
from config import ProjectConfig
from src.core.interfaces import CacheService, CleanupService, TTSEngine, TTSServiceInterface
from engine import QwenTextToSpeech
from services.cache_service import FileCacheService
from services.cleanup_service import FileCleanupService
from services.ssml_processor import SSMLProcessor
from services.tts_service import TTSService
from services.voice_audio_integrity import VoiceAudioIntegrityService
from services.voice_service import VoiceService
from services.text_splitter import get_text_splitter
from infrastructure.audio_converter import PydubAudioConverter
from core.interfaces import AudioConverter


def get_logger() -> logging.Logger:
    return ProjectConfig.get_logger()


def get_tts_engine() -> TTSEngine:
    """Returns the TTS engine instance."""
    return QwenTextToSpeech(
        settings=ProjectConfig.get_settings(), logger=get_logger(), text_splitter=get_text_splitter()
    )


def get_cache_service() -> CacheService:
    """Returns the cache service instance."""
    return FileCacheService(ProjectConfig.get_settings().AUDIO_DIR)


def get_cleanup_service() -> CleanupService:
    """Returns the cleanup service instance."""
    return FileCleanupService()


def get_voice_service() -> VoiceService:
    """Returns the voice service instance."""
    return VoiceService(ProjectConfig.get_settings().VOICES_DIR)


def get_ssml_processor() -> SSMLProcessor:
    return SSMLProcessor(get_voice_service())


def get_voice_audio_integrity() -> VoiceAudioIntegrityService:
    return VoiceAudioIntegrityService(get_voice_service(), get_tts_engine(), get_cache_service())


def get_audio_converter() -> AudioConverter:
    return PydubAudioConverter()


def get_tts_service() -> TTSServiceInterface:
    """Returns the TTS service instance."""
    return TTSService(
        engine=get_tts_engine(),
        cache=get_cache_service(),
        voice_service=get_voice_service(),
        ssml_processor=get_ssml_processor(),
        voice_audio_integrity=get_voice_audio_integrity(),
        audio_converter=get_audio_converter(),
        logger=get_logger(),
    )
