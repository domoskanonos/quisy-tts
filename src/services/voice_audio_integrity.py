from pathlib import Path
from typing import Callable, Awaitable, Optional, Union

from config import ProjectConfig
from src.core.exceptions import AudioGenerationError, ReferenceAudioNotFoundError
from src.core.interfaces import CacheService, TTSEngine, VoiceServiceInterface
from src.services.voice_service import VoiceService
from schemas import TTSParams

logger = ProjectConfig.get_logger()


class VoiceAudioIntegrityService:
    def __init__(self, voice_service: VoiceServiceInterface, engine: TTSEngine, cache: CacheService):
        self.voice_service = voice_service
        self.engine = engine
        self.cache = cache
        self.settings = ProjectConfig.get_settings()
        self.logger = ProjectConfig.get_logger()

    def _is_file_valid(self, voice: dict) -> bool:
        voice_id = voice.get("voice_id")
        if not voice_id:
            return False
        path = Path(self.settings.VOICES_DIR) / VoiceService.get_voice_filename(voice_id)
        return path.exists() and path.stat().st_size > 0

    async def ensure_audio(
        self,
        voice_id: str,
        generator_callback: Optional[Callable[[str, str, str, str, Optional[str]], Awaitable[Union[str, Path]]]] = None,
        force: bool = False,
    ) -> None:
        """Ensure a voice with id `voice_id` has an audio file. If missing,
        synchronously generate it (voice_design) and persist it to the voices DB.
        """
        voice = self.voice_service.get_voice(voice_id)
        if voice is None:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' not found in database.")

        # Check physical existence.
        # The filename is now strictly voice_{voice_id}.wav
        audio_path = Path(self.settings.VOICES_DIR) / VoiceService.get_voice_filename(voice_id)

        # If it exists and is not forced, we are done!
        if audio_path.exists() and audio_path.stat().st_size > 0 and not force:
            return

        self.logger.warning(f"Voice '{voice_id}' has no valid reference audio file. Forcing regeneration.")

        example_text = voice.get("example_text")
        if not example_text:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no example_text.")

        # Build params for voice_design generation
        lang = voice.get("language")
        if not lang:
            # The voice must have an explicit language set — don't fall back.
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no language set")

        # Bypass the callback and generate directly using the engine
        try:
            self.logger.info(f"Automatic generation: starting reference audio generation for voice {voice_id}")

            # Define path directly according to convention
            target_path = Path(self.settings.VOICES_DIR) / VoiceService.get_voice_filename(voice_id)

            # Build params object for engine directly
            params = TTSParams(
                language=lang,
                instruct=voice.get("instruct") or "A clear and natural voice.",
                mode="voice_design",
                model_size="1.7B",
            )

            # Use engine directly
            await self.engine.generate_and_save(example_text, str(target_path), params)
            self.logger.info(f"Generated ref audio directly at: {target_path}")

            if not target_path.exists() or target_path.stat().st_size == 0:
                raise AudioGenerationError(f"Generated audio file for voice '{voice_id}' is empty or missing.")

            self.logger.info(f"Automatic generation: persisted reference audio for voice {voice_id}")

        except Exception as e:
            self.logger.error(f"Failed to generate reference audio for voice '{voice_id}': {e}")
            raise AudioGenerationError(f"Failed to generate reference audio for voice '{voice_id}': {e}") from e
