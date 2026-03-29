from pathlib import Path
from typing import Callable, Any, Awaitable, Optional, Union

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

    def _is_file_valid(self, voice: dict) -> bool:
        filename = voice.get("audio_filename")
        if not filename:
            return False
        path = Path(self.settings.VOICES_DIR) / filename
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

        # Check physical existence if audio is already linked in DB
        # The filename is now strictly voice_{voice_id}.wav
        audio_path = Path(self.settings.VOICES_DIR) / f"voice_{voice_id}.wav"
        if not audio_path.exists() or audio_path.stat().st_size == 0:
            self.logger.warning(f"Voice '{voice_id}' has no reference audio file. Forcing regeneration.")
            force = True

        example_text = voice.get("example_text")
        if not example_text:
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no example_text.")

        # Build params for voice_design generation
        lang = voice.get("language")
        if not lang:
            # The voice must have an explicit language set — don't fall back.
            raise ReferenceAudioNotFoundError(f"Voice '{voice_id}' has no language set")

        gen_params = TTSParams(
            language=lang,
            instruct=voice.get("instruct") or "A clear and natural voice.",
            mode="voice_design",
            model_size="1.7B",
        )

        global_key = self.cache.get_key(example_text, gen_params)
        short = global_key[:12]

        existing_audio = voice.get("audio_filename")
        if existing_audio and (global_key in existing_audio or short in existing_audio) and not force:
            return

        try:
            self.logger.info(f"Automatic generation: starting reference audio generation for voice {voice_id}")
            self.logger.info(f"Debug: generator_callback is {generator_callback}")

            # Use callback to generate (this allows reuse of TTSService.generate_audio)
            if generator_callback is None:
                self.logger.info("Debug: Using default_gen")
                # Default generator uses the engine to generate and save audio to a temp file
                from uuid import uuid4

                async def _default_gen(
                    text: str, language: str, mode: str, model_size: str, instruct: str | None
                ) -> str:
                    self.logger.info("Debug: _default_gen starting")
                    tmp_fn = f"voice_gen_{uuid4().hex}.wav"
                    tmp_path = Path(self.settings.AUDIO_DIR) / tmp_fn
                    # Build params object for engine
                    params = TTSParams(language=language, instruct=instruct, mode=mode, model_size=model_size)
                    res = await self.engine.generate_and_save(text, str(tmp_path), params)
                    self.logger.info(f"Debug: _default_gen finished, result: {res}")
                    return res

                generated_path = await _default_gen(
                    example_text, lang, gen_params.mode, gen_params.model_size, gen_params.instruct
                )
            else:
                self.logger.info("Debug: Using provided callback")
                # generator_callback may be a TTSService.generate_audio-like
                # signature where language is expected to be a str. Use the
                # validated `lang` obtained earlier.
                generated_path = await generator_callback(
                    example_text, lang, gen_params.mode, gen_params.model_size, gen_params.instruct
                )
                self.logger.info(f"Debug: generator_callback finished, result: {generated_path}")

            if not Path(generated_path).exists() or Path(generated_path).stat().st_size == 0:
                raise AudioGenerationError(f"Generated audio file for voice '{voice_id}' is empty or missing.")

            audio_data = Path(generated_path).read_bytes()
            self.voice_service.set_audio(voice_id, audio_data, "generated.wav")
            self.logger.info(f"Automatic generation: persisted reference audio for voice {voice_id}")

        except Exception as e:
            self.logger.error(f"Failed to generate reference audio for voice '{voice_id}': {e}")
            raise AudioGenerationError(f"Failed to generate reference audio for voice '{voice_id}': {e}") from e
