"""TTS orchestration service - Application layer.

This module provides the main entry point for Text-to-Speech operations,
orchestrating components for audio generation, caching, voice management,
SSML processing, and audio format conversion.
"""

from __future__ import annotations
from typing import Any
from pathlib import Path
from collections.abc import AsyncGenerator
import asyncio
from src.core.interfaces import AudioConverter, CacheService, TTSEngine, TTSServiceInterface, VoiceServiceInterface
from src.services.ssml_processor import SSMLProcessor
from src.services.voice_audio_integrity import VoiceAudioIntegrityService
from services.text_splitter import get_text_splitter
from schemas import TTSParams
from services.orchestrator import ssml, generator, streamer


class TTSService(TTSServiceInterface):
    """Orchestrates Text-to-Speech generation and related services.

    This service acts as an application layer in the Hexagonal Architecture,
    coordinating various ports (engines, cache, voice management, etc.)
    to fulfill TTS requests.
    """

    def __init__(
        self,
        engine: TTSEngine,
        cache: CacheService,
        voice_service: VoiceServiceInterface,
        ssml_processor: SSMLProcessor,
        voice_audio_integrity: VoiceAudioIntegrityService,
        audio_converter: AudioConverter,
        logger: Any,
    ) -> None:
        """Initializes the TTS Service with required dependencies.

        Args:
            engine: The TTS engine instance.
            cache: The cache service for storing audio.
            voice_service: The voice management service.
            ssml_processor: The processor for SSML content.
            voice_audio_integrity: Service for checking/ensuring audio integrity for voices.
            audio_converter: Service for converting audio file formats.
            logger: The logger instance.
        """
        self.engine = engine
        self.cache = cache
        self.voice_service: VoiceServiceInterface = voice_service
        self.ssml_processor = ssml_processor
        self.voice_audio_integrity = voice_audio_integrity
        self.audio_converter = audio_converter
        self.logger = logger
        self._locks: dict[str, asyncio.Lock] = {}
        self.text_splitter = get_text_splitter()

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Retrieves or creates an asyncio.Lock for a given cache key.

        This ensures thread-safe atomic operations on cached audio resources.
        """
        # Keep internal logic here as it's stateful
        cache_lock = getattr(self.cache, "get_lock", None)
        if callable(cache_lock):
            try:
                lock = cache_lock(key)
                if isinstance(lock, asyncio.Lock):
                    return lock
            except Exception:
                pass

        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def generate_from_ssml(self, ssml_content: str, base_params: TTSParams) -> tuple[Path, Path]:
        """Generates audio from SSML, performing necessary conversions.

        Args:
            ssml_content: The SSML string.
            base_params: Base generation parameters.

        Returns:
            A tuple containing (WAV file path, MP3 file path).
        """
        wav_path = await ssml.generate_from_ssml(self, ssml_content, base_params)

        # Convert to MP3
        mp3_path = self.audio_converter.convert_to_mp3(wav_path)

        return wav_path, mp3_path

    async def generate_audio(self, *args: Any, **kwargs: Any) -> Path:
        """Generates audio from text/parameters.

        Returns:
            Path to the generated audio file.
        """
        return await generator.generate_audio(self, *args, **kwargs)

    async def generate_stream(self, *args: Any, **kwargs: Any) -> AsyncGenerator[bytes, None]:
        """Generates an audio stream from text/parameters.

        Yields:
            Audio bytes chunks.
        """
        async for chunk in streamer.generate_stream(self, *args, **kwargs):
            yield chunk
