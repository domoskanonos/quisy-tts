"""TTS orchestration service - Application layer."""

from pathlib import Path
from collections.abc import AsyncGenerator
import asyncio
from config import ProjectConfig
from core import CacheService, TTSEngine
from services.voice_service import VoiceService
from services.ssml_processor import SSMLProcessor
from services.sound_effect_service import SoundEffectService
from services.voice_audio_integrity import VoiceAudioIntegrityService
from services.text_splitter import get_text_splitter
from schemas import TTSParams
from services.tts import reference, ssml, generator, streamer

logger = ProjectConfig.get_logger()


class TTSService:
    """Orchestrates TTS generation."""

    def __init__(self, engine: TTSEngine, cache: CacheService) -> None:
        self.engine = engine
        self.cache = cache
        self.text_splitter = get_text_splitter()
        self.voice_service = VoiceService()
        self.ssml_processor = SSMLProcessor(self.voice_service)
        self.sfx_service = SoundEffectService(ProjectConfig.get_settings().AUDIO_DIR)
        self.voice_audio_integrity = VoiceAudioIntegrityService(self.voice_service, engine, cache)
        self._locks: dict[str, asyncio.Lock] = {}
        self._ref_gen_tasks: dict[str, asyncio.Task] = {}
        self._ref_gen_status: dict[str, dict] = {}

    async def _ensure_reference_audio(self, voice_id: str, force: bool = False) -> None:
        await reference.ensure_reference_audio(self, voice_id, force)

    def trigger_reference_audio_generation(self, voice_id: str, force: bool = False) -> None:
        # Check running
        task = self._ref_gen_tasks.get(voice_id)
        if task and not task.done():
            if force:
                try:
                    task.cancel()
                except Exception:
                    pass
            else:
                return
        self._ref_gen_status[voice_id] = {"status": "pending", "message": "queued"}
        t = asyncio.create_task(reference.run_ref_gen_task(self, voice_id, force=force))
        self._ref_gen_tasks[voice_id] = t

    def get_reference_generation_status(self, voice_id: str) -> dict:
        return self._ref_gen_status.get(voice_id, {"status": "pending", "message": "not_started"})

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
