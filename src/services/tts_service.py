"""TTS orchestration service - Application layer."""

from collections.abc import AsyncGenerator
import asyncio
from pathlib import Path

import numpy as np
import soundfile as sf

from config import ProjectConfig
from core import AudioGenerationError, CacheService, TTSEngine
from core.exceptions import ReferenceAudioNotFoundError
from services.voice_service import VoiceService
from services.voice_audio_integrity import VoiceAudioIntegrityService
from services.ssml_processor import SSMLProcessor, TextTask, BreakTask, SoundEffectTask
from services.sound_effect_service import SoundEffectService
from schemas import TTSParams
from schemas.languages import resolve_language
from services.text_splitter import get_text_splitter
from api.websocket_status_manager import status_ws_manager

logger = ProjectConfig.get_logger()


# settings = ProjectConfig.get_settings()  <-- Was removed, but let's re-add as a property or use the class method directly.
# Let's keep it but use the method to access it.
def _get_settings():
    return ProjectConfig.get_settings()


class TTSService:
    """Orchestrates TTS generation with caching and async support.

    This is the main application service that coordinates between
    the API layer and the infrastructure (engine, cache).
    """

    def __init__(self, engine: TTSEngine, cache: CacheService) -> None:
        """Initialize the TTS service.

        Args:
            engine: The TTS engine to use for generation.
            cache: The cache service for storing results.
        """
        self.engine = engine
        self.cache = cache
        self.text_splitter = get_text_splitter()
        self.voice_service = VoiceService()
        self.ssml_processor = SSMLProcessor(self.voice_service)
        self.sfx_service = SoundEffectService(ProjectConfig.get_settings().OUTPUT_DIR)
        self.voice_audio_integrity = VoiceAudioIntegrityService(self.voice_service, engine, cache)
        # locks keyed by chunk cache key to prevent duplicate concurrent generation
        self._locks: dict[str, asyncio.Lock] = {}
        # reference audio generation tasks/status
        self._ref_gen_tasks: dict[str, asyncio.Task] = {}
        self._ref_gen_status: dict[str, dict] = {}

    async def _ensure_reference_audio(self, voice_id: str, force: bool = False) -> None:
        """Ensure reference audio is generated and persisted."""

        # Generator callback that calls self.generate_audio
        async def _generator_callback(text, lang, mode, model_size, instruct):
            return await self.generate_audio(
                text=text,
                language=lang,
                mode=mode,
                model_size=model_size,
                instruct=instruct,
            )

        await self.voice_audio_integrity.ensure_audio(voice_id, _generator_callback, force=force)

    def trigger_reference_audio_generation(self, voice_id: str, force: bool = False) -> None:
        """Start background generation for a voice's reference audio.

        If a generation is already running for the voice, this is a no-op.
        The status can be queried via `get_reference_generation_status`.
        """
        # If already running:
        task = self._ref_gen_tasks.get(voice_id)
        if task and not task.done():
            if force:
                # Cancel existing task and start a new forced generation
                try:
                    task.cancel()
                except Exception:
                    pass
            else:
                return

        # Mark queued status and notify subscribers (fire-and-forget)
        self._ref_gen_status[voice_id] = {"status": "pending", "message": "queued"}
        try:
            asyncio.create_task(
                status_ws_manager.broadcast_to_voice(
                    voice_id, {"type": "ref-gen", "voice_id": voice_id, "status": "queued", "message": "queued"}
                )
            )
        except Exception:
            # best-effort
            pass

        # Create and store task
        t = asyncio.create_task(self._run_ref_gen_task(voice_id, force=force))
        self._ref_gen_tasks[voice_id] = t

    async def _run_ref_gen_task(self, voice_id: str, force: bool = False) -> None:
        """Internal coroutine run by background task to generate and persist audio."""
        # Update running status and broadcast
        self._ref_gen_status[voice_id] = {"status": "running", "message": "starting", "progress": 0}
        try:
            # notify start
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id,
                    {
                        "type": "ref-gen",
                        "voice_id": voice_id,
                        "status": "running",
                        "progress": 0,
                        "message": "starting",
                    },
                )
            except Exception:
                pass
            await self._ensure_reference_audio(voice_id, force=force)

            self._ref_gen_status[voice_id] = {"status": "done", "message": "completed", "progress": 100}
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id,
                    {
                        "type": "ref-gen",
                        "voice_id": voice_id,
                        "status": "done",
                        "progress": 100,
                        "message": "completed",
                    },
                )
            except Exception:
                pass
        except asyncio.CancelledError:
            # Task was cancelled (e.g., due to a forced restart). Record cancelled status
            self._ref_gen_status[voice_id] = {"status": "cancelled", "message": "cancelled"}
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id, {"type": "ref-gen", "voice_id": voice_id, "status": "cancelled", "message": "cancelled"}
                )
            except Exception:
                pass
            # Re-raise so upstream asyncio sees the cancellation
            raise
        except Exception as e:
            self._ref_gen_status[voice_id] = {"status": "failed", "message": str(e)}
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id, {"type": "ref-gen", "voice_id": voice_id, "status": "failed", "message": str(e)}
                )
            except Exception:
                pass

    def get_reference_generation_status(self, voice_id: str) -> dict:
        """Return the current background generation status for voice_id.

        Possible statuses: pending/running/done/failed. If unknown, returns pending.
        """
        return self._ref_gen_status.get(voice_id, {"status": "pending", "message": "not_started"})

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Return an asyncio.Lock for the given key, creating it if necessary.

        Prefer the cache-provided lock when available so locking semantics are
        centralized in the cache implementation.
        """
        # Prefer cache-level lock if implemented
        cache_lock = getattr(self.cache, "get_lock", None)
        if callable(cache_lock):
            try:
                lock = cache_lock(key)
                # Some cache implementations might return non-asyncio locks; ensure type
                if isinstance(lock, asyncio.Lock):
                    return lock
            except Exception:
                # Fall back to local lock map on any error
                pass

        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def generate_from_ssml(self, ssml_content: str, base_params: TTSParams) -> Path:
        """Generate audio from SSML content."""
        tasks = self.ssml_processor.parse(ssml_content)

        combined_audio = []
        sample_rate = 24000

        for task in tasks:
            if isinstance(task, TextTask):
                vs = VoiceService()
                voice = vs.get_voice(task.speaker)
                if not voice:
                    raise AudioGenerationError(f"Speaker ID {task.speaker} not found")

                # Use base mode for all DB-backed voices (Voice Cloning)
                params = base_params.model_copy()
                params.mode = "base"
                params.reference_audio = voice["id"]
                params.instruct = voice.get("instruct")

                # Ensure reference audio exists (cloning requires audio_filename)
                await self._ensure_reference_audio(voice["id"])

                # Generate audio chunk
                chunk_path = await self.generate_audio(
                    task.text,
                    params.language or "German",
                    "base",
                    params.model_size or "1.7B",
                    reference_audio=voice["id"],
                    ref_text=voice.get("example_text"),
                    instruct=params.instruct,
                )

                data, sr = sf.read(str(chunk_path))
                combined_audio.append(data)
                sample_rate = sr
            elif isinstance(task, BreakTask):
                silence_samples = int(sample_rate * (task.duration_ms / 1000))
                combined_audio.append(np.zeros(silence_samples, dtype=np.float32))
            elif isinstance(task, SoundEffectTask):
                sfx_path = await self.sfx_service.generate(task.description)
                data, sr = sf.read(str(sfx_path))
                # Resample if needed
                if sr != sample_rate:
                    import librosa

                    data = librosa.resample(data, orig_sr=sr, target_sr=sample_rate)
                combined_audio.append(data)

        final_audio = np.concatenate(combined_audio)

        # Save to a new filename based on hash
        import hashlib

        ssml_key = hashlib.sha256(ssml_content.encode()).hexdigest()[:12]
        output_path = ProjectConfig.get_settings().OUTPUT_DIR / f"ssml_{ssml_key}.wav"

        sf.write(str(output_path), final_audio, sample_rate)
        return output_path

    async def generate_audio(  # noqa: PLR0913
        self,
        text: str,
        language: str,
        mode: str,
        model_size: str,
        reference_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        speaker: str | None = None,
    ) -> Path:
        """Generate audio from text with caching and smart splitting.

        Args:
            text: The text to convert to speech.
            language: Language code or name.
            mode: Generation mode.
            model_size: Model size.
            reference_audio: Reference audio filename.
            ref_text: Transcript of reference audio.
            instruct: Style instruction.
            speaker: Speaker ID.

        Returns:
            Path to the generated audio file.

        Raises:
            AudioGenerationError: If generation fails.
        """
        # Resolve canonical language for engine and ensure instruct contains an explicit
        # language directive when appropriate. This helps avoid cases where style
        # prompts in English cause the model to produce English output for German
        # voices.
        resolved = resolve_language(language)
        final_instruct = instruct
        try:
            if final_instruct and resolved == "german":
                # If instruct doesn't already mention the language, prefix a German directive
                low = final_instruct.lower()
                if not ("sprich" in low or "auf deutsch" in low or "in german" in low or "auf deutsch" in low):
                    final_instruct = "Sprich auf Deutsch. " + final_instruct
        except Exception:
            # Be defensive: fallback to original instruct
            final_instruct = instruct

        # Automatically resolve ref_text from DB if cloning
        if not ref_text and reference_audio:
            vs = VoiceService()
            voice = vs.get_voice(reference_audio)
            if voice:
                ref_text = voice.get("example_text")
                # Ensure reference audio exists (cloning requires audio_filename)
                await self._ensure_reference_audio(reference_audio)

        params = TTSParams(
            language=resolved,
            reference_audio=reference_audio,
            ref_text=ref_text,
            mode=mode,
            model_size=model_size,
            instruct=final_instruct,
            speaker=speaker,
        )

        logger.debug(f"TTS params: language={params.language}, mode={params.mode}, model_size={params.model_size}")

        # 1. Check global cache for the full text
        global_key = self.cache.get_key(text, params)
        logger.info(f"Checking global cache for key: {global_key[:8]}...")
        logger.debug(f"Global cache full key: {global_key}")
        if cached_path := self.cache.get(global_key):
            logger.info(f"Global cache hit for key {global_key[:8]} -> {cached_path.name}")
            return cached_path

        # 2. Split text into chunks
        chunks = self.text_splitter.split(text, params.language or "german")
        if not chunks:
            raise AudioGenerationError("Text is empty after splitting")

        logger.info(f"Text split into {len(chunks)} chunks for key {global_key[:8]}...")

        chunk_paths: list[Path] = []

        # 3. Process each chunk
        for i, chunk_text in enumerate(chunks):
            # Calculate hash for this specific chunk
            chunk_key = self.cache.get_key(chunk_text, params)

            # Fast path: check chunk cache (no lock)
            if chunk_path := self.cache.get(chunk_key):
                logger.info(f"Chunk cache hit for key {chunk_key[:8]} ({i + 1}/{len(chunks)}) -> {chunk_path.name}")
                logger.debug(f"Chunk full key: {chunk_key}")
                chunk_paths.append(chunk_path)
                continue

            # Obtain per-chunk lock to avoid duplicate concurrent generation
            lock = self._get_lock(chunk_key)
            try:
                async with lock:
                    # Re-check inside the lock
                    if chunk_path := self.cache.get(chunk_key):
                        logger.info(f"Chunk cache hit inside lock for key: {chunk_key[:8]}...")
                        chunk_paths.append(chunk_path)
                    else:
                        # Generate if still missed
                        logger.info(f"Generating chunk {i + 1}/{len(chunks)} for key: {chunk_key[:8]}...")
                        logger.debug(f"Generating chunk full key: {chunk_key}")
                        filename = f"cache_{chunk_key}.wav"
                        output_path = ProjectConfig.get_settings().OUTPUT_DIR / filename

                        try:
                            result_path = await self.engine.generate_and_save(
                                chunk_text,
                                str(output_path),
                                params,
                            )
                            generated_path = Path(result_path)

                            # Register in cache
                            self.cache.set(chunk_key, generated_path)
                            chunk_paths.append(generated_path)
                            logger.info(
                                f"Generated chunk {i + 1}/{len(chunks)} and cached as {generated_path.name} (key {chunk_key[:8]})"
                            )

                        except Exception as e:
                            logger.error(f"Failed to generate chunk {i + 1}: {e}")
                            # If generation was cancelled, remove any partial output file
                            if isinstance(e, asyncio.CancelledError):
                                try:
                                    if output_path.exists():
                                        output_path.unlink()
                                except Exception:
                                    pass
                                raise
                            raise AudioGenerationError(f"Chunk generation failed: {e}") from e
            finally:
                # Cleanup lock to prevent unbounded growth of the lock map.
                try:
                    if not lock.locked():
                        # It's safe to remove; if another coroutine creates a new lock concurrently
                        # it will replace this entry.
                        del self._locks[chunk_key]
                except Exception:
                    # Be defensive: do not raise from cleanup
                    pass

        # 4. Combine chunks if necessary
        if len(chunks) == 1:
            # Single chunk: The global result IS the chunk result
            # We just need to make sure the global key points to it
            # Since we can't easily symlink on all OSes reliably or might want separate files,
            # we'll just copy it to the global cache name if it differs, or index it.
            # But wait, our cache service expects a specific filename format "cache_{key}.wav".
            # The chunk file is "cache_{chunk_key}.wav".
            # If text == chunk_text, then global_key == chunk_key.
            # So it's already there!
            return chunk_paths[0]

        # Multiple chunks: Concatenate
        try:
            combined_audio = []
            sample_rate = 24000  # Default, will be updated from files

            silence_secs = 0.15

            for i, path in enumerate(chunk_paths):
                data, sr = sf.read(str(path))
                sample_rate = sr
                combined_audio.append(data)

                # Add silence between chunks
                if i < len(chunk_paths) - 1:
                    silence_samples = int(silence_secs * sample_rate)
                    combined_audio.append(np.zeros(silence_samples, dtype=data.dtype))

            final_audio = np.concatenate(combined_audio)

            # Save to global cache path
            global_filename = f"cache_{global_key}.wav"
            global_path = ProjectConfig.get_settings().OUTPUT_DIR / global_filename

            sf.write(str(global_path), final_audio, sample_rate)

            # Register global cache hit (file is already in place)
            logger.info(f"Combined {len(chunks)} chunks into {global_filename}")
            return global_path

        except Exception as e:
            logger.error(f"Failed to combine chunks: {e}")
            raise AudioGenerationError(f"Audio concatenation failed: {e}") from e

    async def generate_stream(  # noqa: PLR0913
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
        """Generate audio stream from text with caching.

        Args:
            text: The text to convert to speech.
            language: Language code or name.
            mode: Generation mode.
            model_size: Model size.
            reference_audio: Reference audio filename.
            ref_text: Transcript of reference audio.
            instruct: Style instruction.
            speaker: Speaker ID.
            chunk_size: Size of each chunk in bytes.

        Yields:
            Audio data chunks as bytes.
        """
        params = TTSParams(
            language=resolve_language(language),
            reference_audio=reference_audio,
            ref_text=ref_text,
            mode=mode,
            model_size=model_size,
            instruct=instruct,
            speaker=speaker,
        )

        global_key = self.cache.get_key(text, params)
        logger.info(f"Streaming for key: {global_key[:8]}...")
        logger.debug(f"Streaming global key full: {global_key}")

        # 1. Check global cache first
        if cached_path := self.cache.get(global_key):
            logger.info("Global cache hit for stream.")
            with sf.SoundFile(str(cached_path)) as f:
                while True:
                    data = f.read(dtype="int16", frames=chunk_size // 2)  # chunk_size bytes -> frames
                    if len(data) == 0:
                        break
                    yield data.tobytes()
            return

        # 2. Split and process chunks
        chunks = self.text_splitter.split(text, params.language or "german")
        logger.info(f"Streaming will process {len(chunks)} chunks for key {global_key[:8]}")

        # We need to collect paths to potentially save global cache at the end?
        # Streaming is often for immediate playback, but if we can cache the result, great.
        # But we can't easily reconstruct the global audio without keeping all chunks.
        # Let's just cache chunks for now, as that satisfies "intermediate texts".
        # If the user requests the full text later, `generate_audio` will re-combine the cached chunks.

        for i, chunk_text in enumerate(chunks):
            chunk_key = self.cache.get_key(chunk_text, params)

            # Fast path
            chunk_path = self.cache.get(chunk_key)
            if chunk_path:
                logger.info(
                    f"Stream: chunk cache hit for key {chunk_key[:8]} ({i + 1}/{len(chunks)}) -> {chunk_path.name}"
                )
                logger.debug(f"Stream chunk full key: {chunk_key}")
            else:
                logger.info(f"Stream: cache miss for chunk {i + 1}/{len(chunks)} (key {chunk_key[:8]}) - generating")
                lock = self._get_lock(chunk_key)
                async with lock:
                    # Re-check inside lock
                    chunk_path = self.cache.get(chunk_key)
                    if chunk_path:
                        logger.info(
                            f"Stream: chunk cache hit inside lock for key {chunk_key[:8]} ({i + 1}/{len(chunks)}) -> {chunk_path.name}"
                        )
                    else:
                        # Generate and save chunk
                        output_path = ProjectConfig.get_settings().OUTPUT_DIR / f"cache_{chunk_key}.wav"
                        try:
                            logger.debug(f"Stream: generating chunk full key: {chunk_key}")
                            result_path = await self.engine.generate_and_save(
                                chunk_text,
                                str(output_path),
                                params,
                            )
                            chunk_path = Path(result_path)
                            self.cache.set(chunk_key, chunk_path)
                            logger.info(
                                f"Stream: generated and cached chunk {i + 1}/{len(chunks)} -> {chunk_path.name} (key {chunk_key[:8]})"
                            )
                        except Exception as e:
                            logger.error(f"Failed to generate chunk {i} for stream: {e}")
                            raise AudioGenerationError(f"Stream generation failed: {e}") from e

            # Stream the chunk file
            logger.info(f"Streaming chunk {i + 1}/{len(chunks)} from {chunk_path.name}")
            with sf.SoundFile(str(chunk_path)) as f:
                while True:
                    data = f.read(dtype="int16", frames=chunk_size // 2)
                    if len(data) == 0:
                        break
                    yield data.tobytes()

            # Yield silence between chunks if not last
            if i < len(chunks) - 1:
                silence_secs = 0.15
                # 24kHz * 0.15 = 3600 samples. 16bit = 2 bytes/sample.
                # We need to yield bytes.
                # Retrieve sample rate from file just read
                sr = 24000  # default
                try:
                    info = sf.info(str(chunk_path))
                    sr = info.samplerate
                except Exception:
                    pass

                silence_samples = int(sr * silence_secs)
                silence_bytes = np.zeros(silence_samples, dtype=np.int16).tobytes()
                yield silence_bytes
