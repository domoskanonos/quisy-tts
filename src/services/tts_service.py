"""TTS orchestration service - Application layer."""

from __future__ import annotations
from typing import Any
from pathlib import Path
from collections.abc import AsyncGenerator
import asyncio
from src.core.interfaces import CacheService, TTSEngine, TTSServiceInterface, VoiceServiceInterface
from src.services.ssml_processor import SSMLProcessor
from src.services.voice_audio_integrity import VoiceAudioIntegrityService
from services.text_splitter import get_text_splitter
from schemas import TTSParams
from services.tts import ssml, generator, streamer


class TTSService(TTSServiceInterface):
    """Orchestrates TTS generation."""

    def __init__(
        self,
        engine: TTSEngine,
        cache: CacheService,
        voice_service: VoiceServiceInterface,
        ssml_processor: SSMLProcessor,
        voice_audio_integrity: VoiceAudioIntegrityService,
        logger: Any,
    ) -> None:
        self.engine = engine
        self.cache = cache
        self.voice_service: VoiceServiceInterface = voice_service
        self.ssml_processor = ssml_processor
        self.voice_audio_integrity = voice_audio_integrity
        self.logger = logger
        self._locks: dict[str, asyncio.Lock] = {}
        self.text_splitter = get_text_splitter()

    def _get_lock(self, key: str) -> asyncio.Lock:
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

    async def generate_from_ssml(self, ssml_content: str, base_params: TTSParams) -> Path:
        return await ssml.generate_from_ssml(self, ssml_content, base_params)

    async def generate_audio(self, *args, **kwargs) -> Path:
        return await generator.generate_audio(self, *args, **kwargs)

    async def generate_stream(self, *args, **kwargs) -> AsyncGenerator[bytes, None]:
        """Generate audio stream."""
        async for chunk in streamer.generate_stream(self, *args, **kwargs):
            yield chunk
