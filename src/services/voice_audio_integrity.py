from pathlib import Path
from typing import Callable, Any

from config import ProjectConfig
from core import AudioGenerationError, ReferenceAudioNotFoundError, CacheService, TTSEngine
from services.voice_service import VoiceService
from schemas import TTSParams

logger = ProjectConfig.get_logger()


class VoiceAudioIntegrityService:
    def __init__(self, voice_service: VoiceService, engine: TTSEngine, cache: CacheService):
        self.voice_service = voice_service
        self.engine = engine
        self.cache = cache
        self.settings = ProjectConfig.get_settings()
        self.logger = ProjectConfig.get_logger()

    async def ensure_audio(
        self, voice_id: str, generator_callback: Callable[[str, str, str, str, str | None], Any], force: bool = False
    ) -> None:
        """Ensure a voice with id `voice_id` has an audio file. If missing,
        synchronously generate it (voice_design) and persist it to the voices DB.
        """
        voice = self.voice_service.get_voice(voice_id)
        if voice is None:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' not found in database.")

        example_text = voice.get("example_text")
        if not example_text:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no example_text.")

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

        existing_audio = voice.get("audio_filename")
        if existing_audio and (global_key in existing_audio or short in existing_audio) and not force:
            return

        try:
            self.logger.info(f"Automatic generation: starting reference audio generation for voice {voice_id}")

            # Use callback to generate (this allows reuse of TTSService.generate_audio)
            generated_path = await generator_callback(
                example_text, gen_params.language, gen_params.mode, gen_params.model_size, gen_params.instruct
            )

            if not Path(generated_path).exists() or Path(generated_path).stat().st_size == 0:
                raise AudioGenerationError(f"Generated audio file for voice '{voice_id}' is empty or missing.")

            target_path = Path(self.settings.VOICES_DIR) / expected_voice_fn
            target_path.write_bytes(Path(generated_path).read_bytes())

            self.voice_service.set_audio(
                voice_id, target_path.read_bytes(), target_path.name, audio_filename=expected_voice_fn
            )
            self.logger.info(f"Automatic generation: persisted reference audio for voice {voice_id}")

        except Exception as e:
            raise AudioGenerationError(f"Failed to generate reference audio for voice '{voice_id}': {e}") from e
