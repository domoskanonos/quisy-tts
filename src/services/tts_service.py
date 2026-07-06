"""TTS orchestration service - Application layer.

This module provides the main entry point for Text-to-Speech operations,
orchestrating components for audio generation, caching, voice management,
SSML processing, and audio format conversion.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from schemas import TTSParams
from services.orchestrator import generator, ssml, streamer
from src.core.interfaces import (
    AudioConverter,
    CacheService,
    TTSEngineInterface,
    TTSServiceInterface,
    VoiceServiceInterface,
)
from src.services.ssml_processor import SSMLProcessor
from src.services.voice_audio_integrity import VoiceAudioIntegrityService


class TTSService(TTSServiceInterface):
    """Orchestrates Text-to-Speech generation and related services.

    This service acts as an application layer in the Hexagonal Architecture,
    coordinating various ports (engines, cache, voice management, etc.)
    to fulfill TTS requests.
    """

    def __init__(
        self,
        engine: TTSEngineInterface,
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
            except Exception as e:
                self.logger.warning(f"Failed to get lock from cache service: {e}")

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

    async def generate_audio(
        self,
        text: str,
        language: str,
        mode: str,
        model_size: str,
        reference_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        speaker: str | None = None,
        skip_integrity_check: bool = False,
    ) -> Path:
        """Generates audio from text/parameters.

        Returns:
            Path to the generated audio file.
        """
        return await generator.generate_audio(
            self,
            text=text,
            language=language,
            mode=mode,
            model_size=model_size,
            reference_audio=reference_audio,
            ref_text=ref_text,
            instruct=instruct,
            speaker=speaker,
            skip_integrity_check=skip_integrity_check,
        )

    def generate_stream(
        self,
        text: str,
        language: str,
        mode: str,
        model_size: str,
        reference_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        speaker: str | None = None,
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """Generates an audio stream from text/parameters.

        Yields:
            Audio bytes chunks.
        """
        return streamer.generate_stream(
            self,
            text=text,
            language=language,
            mode=mode,
            model_size=model_size,
            reference_audio=reference_audio,
            ref_text=ref_text,
            instruct=instruct,
            speaker=speaker,
            chunk_size=chunk_size,
        )
