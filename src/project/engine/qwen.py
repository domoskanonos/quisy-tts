"""Qwen3-TTS engine implementation."""

import hashlib
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from project.audio.processor import AudioUtils, SoxAudioProcessor
from project.config import ProjectConfig
from project.core import TTSEngine
from project.models.manager import ModelManager
from project.schemas import TTSParams


logger = ProjectConfig.get_logger()


@lru_cache(maxsize=16)
def _load_cached_audio(path: str) -> tuple:
    """Load audio file with caching to avoid repeated disk I/O."""
    logger.info(f"Loading audio file into cache: {path}")
    data, sr = sf.read(path)
    return (data, sr)


class QwenTextToSpeech(TTSEngine):
    """Qwen3-TTS implementation of the TTSEngine interface."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()
        # Cache for voice clone prompts (keyed by ref_audio + ref_text hash)
        self._voice_prompts: dict[str, object] = {}

    def generate_audio(
        self, text: str, params: TTSParams = None
    ) -> tuple[torch.Tensor, int]:
        """Generates audio waveform for the given text and parameters."""
        if params is None:
            params = TTSParams()

        logger.info(
            f"Starting audio generation | Mode: {params.mode} | "
            f"Text Length: {len(text)} | Language: {params.language}"
        )

        model = ModelManager.get_model(mode=params.mode, size=params.model_size)
        ref_audio_data = self._get_reference_audio(params)

        try:
            # Generation parameters for optimal speed/quality
            gen_kwargs = {
                "do_sample": True,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_new_tokens": 2048,  # Limit generation length
            }

            if params.mode == "voice_design":
                audio_list, sr = model.generate_voice_design(
                    text,
                    instruct=params.instruct,
                    language=params.resolved_language,
                    **gen_kwargs,
                )
            elif params.mode == "custom_voice":
                audio_list, sr = model.generate_custom_voice(
                    text,
                    speaker=params.speaker,
                    instruct=params.instruct,
                    language=params.resolved_language,
                    **gen_kwargs,
                )
            else:  # base / voice cloning
                xvec = params.ref_text is None or params.ref_text == ""
                voice_prompt = self._get_or_create_voice_prompt(
                    model, ref_audio_data, params.ref_text, xvec
                )
                audio_list, sr = model.generate_voice_clone(
                    text,
                    language=params.resolved_language,
                    voice_clone_prompt=voice_prompt,
                    **gen_kwargs,
                )

            if not audio_list:
                raise ValueError("Model returned empty audio list")

            final_audio = torch.from_numpy(audio_list[0]).unsqueeze(0)
            logger.info(f"Audio generation successful. Shape: {final_audio.shape}")

            return final_audio, sr

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def generate_and_save(
        self, text: str, output_path: str, params: TTSParams = None
    ) -> str:
        """Generates audio and saves it to a file with post-processing."""
        if params is None:
            params = TTSParams()

        waveform, sr = self.generate_audio(text, params)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        temp_path = Path(output_path).with_suffix(".tmp.wav")
        AudioUtils.save_waveform(waveform, sr, str(temp_path))

        if SoxAudioProcessor.apply_effects(str(temp_path), output_path):
            # Sox success, output_path exists, remove temp
            if temp_path.exists():
                temp_path.unlink()
        # Sox failed/missing, use temp file as output
        elif temp_path.exists():
            if Path(output_path).exists():
                Path(output_path).unlink()
            temp_path.replace(output_path)

        logger.info(f"Audio saved to {output_path}")
        return output_path

    def generate_audio_stream(
        self, text: str, params: TTSParams = None, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Generates audio and yields it in chunks."""
        logger.info("Starting audio stream generation...")
        waveform, sr = self.generate_audio(text, params)

        audio_np = waveform.squeeze().cpu().numpy()
        audio_int16 = (audio_np * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i : i + chunk_size]

    def _get_reference_audio(self, params: TTSParams) -> tuple | None:
        """Helper to load reference audio."""
        if not params.reference_audio or params.reference_audio == "string":
            if params.mode == "base":
                # Try configured default first
                default_ref = self.settings.DEFAULT_REFERENCE_AUDIO
                if default_ref:
                    ref_path = self.settings.VOICES_DIR / default_ref
                    if ref_path.exists():
                        logger.info(
                            f"Using configured default reference audio: {default_ref}"
                        )
                        return _load_cached_audio(str(ref_path))
                    logger.warning(
                        f"Configured default reference audio not found: {default_ref}. "
                        "Falling back to directory scan."
                    )

                # Fallback: scan directory
                voices = list(self.settings.VOICES_DIR.glob("*.wav"))
                if voices:
                    logger.info(f"Using fallback reference audio: {voices[0].name}")
                    return _load_cached_audio(str(voices[0]))

                logger.error(
                    f"Base mode requires reference audio. "
                    f"No .wav files found in {self.settings.VOICES_DIR.absolute()}"
                )
            return None

        ref_path = self.settings.VOICES_DIR / params.reference_audio
        if ref_path.exists():
            logger.info(f"Using reference audio: {ref_path.name}")
            return _load_cached_audio(str(ref_path))

        logger.warning(f"Reference audio not found: {ref_path}")
        return None

    def _get_or_create_voice_prompt(
        self,
        model: object,
        ref_audio: tuple | None,
        ref_text: str | None,
        x_vector_only: bool,
    ) -> object:
        """Get cached voice clone prompt or create a new one.

        Uses Qwen3-TTS's create_voice_clone_prompt() to avoid recomputing
        speaker embeddings on every generation call.

        Args:
            model: The Qwen3TTSModel instance.
            ref_audio: Tuple of (audio_data, sample_rate) or None.
            ref_text: Transcript of reference audio.
            x_vector_only: Whether to use x-vector only mode.

        Returns:
            Cached or newly created voice clone prompt.
        """
        if ref_audio is None:
            return None

        # Create a cache key based on ref_audio identity and ref_text
        audio_data, sr = ref_audio
        audio_hash = hashlib.md5(audio_data.tobytes()[:4096]).hexdigest()[:8]
        cache_key = f"{audio_hash}:{ref_text or ''}:{x_vector_only}"

        if cache_key in self._voice_prompts:
            logger.info(f"Using cached voice prompt: {cache_key[:16]}...")
            return self._voice_prompts[cache_key]

        logger.info(f"Creating new voice prompt: {cache_key[:16]}...")
        try:
            prompt = model.create_voice_clone_prompt(
                ref_audio=ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only,
            )
            self._voice_prompts[cache_key] = prompt
            return prompt
        except Exception as e:
            logger.warning(f"Failed to create voice prompt, falling back: {e}")
            return None
