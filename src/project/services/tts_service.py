"""TTS orchestration service - Application layer."""

import asyncio
import uuid
from collections.abc import Generator
from pathlib import Path

from project.config import ProjectConfig
from project.core import AudioGenerationError, CacheService, TTSEngine
from project.schemas import TTSParams
from project.schemas.languages import resolve_language


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
    ) -> Path:
        """Generate audio from text with caching.

        Args:
            text: The text to convert to speech.
            language: Language code or name.
            mode: Generation mode (base, voice_design, custom_voice).
            model_size: Model size (0.6B, 1.7B).
            reference_audio: Reference audio filename for voice cloning.
            ref_text: Transcript of reference audio.
            instruct: Style instruction for voice design.
            speaker: Speaker ID for custom voice.

        Returns:
            Path to the generated audio file.

        Raises:
            AudioGenerationError: If generation fails.
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

        # Check cache
        cache_key = self.cache.get_key(text, params)
        if cached := self.cache.get(cache_key):
            return cached

        # Generate
        filename = f"{uuid.uuid4()}.wav"
        output_path = settings.OUTPUT_DIR / filename

        try:
            loop = asyncio.get_event_loop()
            result_path = await loop.run_in_executor(
                None,
                self.engine.generate_and_save,
                text,
                str(output_path),
                params,
            )
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise AudioGenerationError(str(e)) from e

        if not result_path or not Path(result_path).exists():
            raise AudioGenerationError("Generation returned no file")

        # Cache the result
        self.cache.set(cache_key, Path(result_path))

        return Path(result_path)

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
    ) -> Generator[bytes, None, None]:
        """Generate audio stream from text.

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

        return self.engine.generate_audio_stream(text, params, chunk_size)
