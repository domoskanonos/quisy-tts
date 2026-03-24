"""TTS orchestration service - Application layer."""

from collections.abc import AsyncGenerator
from pathlib import Path

import numpy as np
import soundfile as sf

from config import ProjectConfig
from core import AudioGenerationError, CacheService, TTSEngine
from schemas import TTSParams
from schemas.languages import resolve_language
from services.text_splitter import get_text_splitter

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
        if cached_path := self.cache.get(global_key):
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

            # Check chunk cache
            if chunk_path := self.cache.get(chunk_key):
                chunk_paths.append(chunk_path)
                continue

            # Generate if missed
            # We use a temporary filename based on the hash to ensure uniqueness
            filename = f"cache_{chunk_key}.wav"
            output_path = settings.OUTPUT_DIR / filename

            try:
                result_path = await self.engine.generate_and_save(
                    chunk_text,
                    str(output_path),
                    params,
                )
                generated_path = Path(result_path)

                # Register in cache (though we wrote directly to cache location effectively)
                self.cache.set(chunk_key, generated_path)
                chunk_paths.append(generated_path)

            except Exception as e:
                logger.error(f"Failed to generate chunk {i}: {e}")
                raise AudioGenerationError(f"Chunk generation failed: {e}") from e

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

        # We need to collect paths to potentially save global cache at the end?
        # Streaming is often for immediate playback, but if we can cache the result, great.
        # But we can't easily reconstruct the global audio without keeping all chunks.
        # Let's just cache chunks for now, as that satisfies "intermediate texts".
        # If the user requests the full text later, `generate_audio` will re-combine the cached chunks.

        for i, chunk_text in enumerate(chunks):
            chunk_key = self.cache.get_key(chunk_text, params)

            chunk_path = self.cache.get(chunk_key)
            if not chunk_path:
                # Generate and save chunk
                output_path = settings.OUTPUT_DIR / f"cache_{chunk_key}.wav"
                try:
                    result_path = await self.engine.generate_and_save(
                        chunk_text,
                        str(output_path),
                        params,
                    )
                    chunk_path = Path(result_path)
                    self.cache.set(chunk_key, chunk_path)
                except Exception as e:
                    logger.error(f"Failed to generate chunk {i} for stream: {e}")
                    raise AudioGenerationError(f"Stream generation failed: {e}") from e

            # Stream the chunk file
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
