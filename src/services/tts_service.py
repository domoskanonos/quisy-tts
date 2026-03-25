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
from schemas import TTSParams
from schemas.languages import resolve_language
from services.text_splitter import get_text_splitter
from api.websocket_status_manager import status_ws_manager

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


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
        # locks keyed by chunk cache key to prevent duplicate concurrent generation
        self._locks: dict[str, asyncio.Lock] = {}
        # reference audio generation tasks/status
        self._ref_gen_tasks: dict[str, asyncio.Task] = {}
        self._ref_gen_status: dict[str, dict] = {}

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

            await self._ensure_reference_audio_for_voice_id(voice_id, force=force)

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

    async def _ensure_reference_audio_for_voice_id(self, voice_id: str, force: bool = False) -> None:
        """Ensure a voice with id `voice_id` has an audio file. If missing,
        synchronously generate it (voice_design) and persist it to the voices DB.

        This blocks the calling request until generation completes so the
        subsequent base cloning has a concrete reference audio available.
        """
        vs = VoiceService()
        voice = vs.get_voice(voice_id)
        if voice is None:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' not found in database.")

        # Compute expected cache key for the voice's example_text + params
        example_text = voice.get("example_text")
        if not example_text:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no example_text to generate audio from.")

        # Build params for voice_design generation
        gen_params = TTSParams(
            language=voice.get("language", "german"),
            instruct=voice.get("instruct") or "A clear and natural voice.",
            mode="voice_design",
            model_size="1.7B",
        )

        global_key = self.cache.get_key(example_text, gen_params)
        short = global_key[:12]
        expected_voice_fn = f"voice_{voice_id}_{short}.wav"

        # If existing audio matches expected and not forcing, skip generation
        existing_audio = voice.get("audio_filename")
        if existing_audio and (global_key in existing_audio or short in existing_audio) and not force:
            logger.info(f"Reference audio for voice {voice_id} is up-to-date (key {short}). Skipping generation.")
            return

        # Need example_text to generate via voice_design (already checked above)

        # Prepare to generate via existing pipeline (generate_audio) which will store chunk cache files
        try:
            logger.info(f"Automatic generation: starting reference audio generation for voice {voice_id} (key {short})")
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id,
                    {
                        "type": "ref-gen",
                        "voice_id": voice_id,
                        "status": "running",
                        "progress": 10,
                        "message": "loading_model",
                    },
                )
            except Exception:
                pass

            # Use TTSService.generate_audio to leverage existing cache key generation and chunking.
            generated_path = await self.generate_audio(
                text=example_text,
                language=gen_params.language,
                mode=gen_params.mode,
                model_size=gen_params.model_size,
                instruct=gen_params.instruct,
            )

            # generated_path is the cached global audio (cache_{global_key}.wav) or combined file.
            # Copy it into voices dir with a deterministic name containing the short key.
            target_path = vs._voices_dir / expected_voice_fn
            target_path.write_bytes(Path(generated_path).read_bytes())

            # Persist via DB using set_audio override (new signature supports explicit filename)
            vs.set_audio(voice_id, target_path.read_bytes(), target_path.name, audio_filename=expected_voice_fn)

            logger.info(
                f"Automatic generation: finished and persisted reference audio for voice {voice_id} as {expected_voice_fn}"
            )
            try:
                await status_ws_manager.broadcast_to_voice(
                    voice_id,
                    {
                        "type": "ref-gen",
                        "voice_id": voice_id,
                        "status": "running",
                        "progress": 90,
                        "message": "persisted",
                    },
                )
            except Exception:
                pass

        except Exception as e:
            raise AudioGenerationError(f"Failed to generate reference audio for voice '{voice_id}': {e}") from e

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
                        output_path = settings.OUTPUT_DIR / filename

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
            global_path = settings.OUTPUT_DIR / global_filename

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
                        output_path = settings.OUTPUT_DIR / f"cache_{chunk_key}.wav"
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
