"""
QuisyTTS Library Client.

Provides a simplified interface to interact with the core TTS engine and services
without requiring a running FastAPI/MCP server.
"""

import logging
from typing import Any
from src.config import ProjectConfig
from src.core.interfaces import CacheService, CleanupService, TTSEngine, TTSServiceInterface
from src.engine import QwenTextToSpeech
from src.services.cache_service import FileCacheService
from src.services.cleanup_service import FileCleanupService
from src.services.ssml_processor import SSMLProcessor
from src.services.tts_service import TTSService
from src.services.voice_audio_integrity import VoiceAudioIntegrityService
from src.services.voice_service import VoiceService
from src.services.text_splitter import get_text_splitter


class QuisyTTS:
    """Main client class for the QuisyTTS library."""

    def __init__(self, config: Any = None):
        self.settings = config or ProjectConfig.get_settings()
        self.logger = ProjectConfig.get_logger()
        self._voice_service = None
        self._tts_service = None

    @property
    def voice_service(self) -> VoiceService:
        if self._voice_service is None:
            self._voice_service = VoiceService(self.settings.VOICES_DIR)
        return self._voice_service

    @property
    def tts_service(self) -> TTSServiceInterface:
        if self._tts_service is None:
            # Reusing the existing service instantiation logic
            engine = QwenTextToSpeech(self.settings, self.logger, get_text_splitter())
            cache = FileCacheService(self.settings.AUDIO_DIR)
            ssml_processor = SSMLProcessor(self.voice_service)
            integrity = VoiceAudioIntegrityService(self.voice_service, engine, cache)

            self._tts_service = TTSService(
                engine=engine,
                cache=cache,
                voice_service=self.voice_service,
                ssml_processor=ssml_processor,
                voice_audio_integrity=integrity,
                logger=self.logger,
            )
        return self._tts_service

    def shutdown(self):
        """Cleanup resources."""
        # Add cleanup logic if needed
        pass
