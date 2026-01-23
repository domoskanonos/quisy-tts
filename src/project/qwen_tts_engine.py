from collections.abc import Generator
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from project.audio.processor import AudioUtils, SoxAudioProcessor
from project.config import ProjectConfig
from project.models.manager import ModelManager
from project.schemas import TTSParams


logger = ProjectConfig.get_logger()


class QwenTextToSpeech:
    """Orchestrates TTS generation using modular components."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()

    def generate_audio(
        self, text: str, params: TTSParams = None
    ) -> tuple[torch.Tensor, int]:
        """Generates audio bytes for the given text and parameters."""
        if params is None:
            params = TTSParams()

        # 1. Log Generation
        logger.info(
            f"Starting audio generation | Mode: {params.mode} | "
            f"Text Length: {len(text)} | Language: {params.language_id}"
        )

        # 2. Get Model
        model = ModelManager.get_model(mode=params.mode, size=params.model_size)

        # 3. Load Reference Audio (if needed)
        ref_audio_data = self._get_reference_audio(params)

        # 4. Generate
        try:
            if params.mode == "voice_design":
                audio_list, sr = model.generate_voice_design(
                    text, instruct=params.instruct, language=params.resolved_language
                )
            elif params.mode == "custom_voice":
                audio_list, sr = model.generate_custom_voice(
                    text,
                    speaker=params.speaker,
                    instruct=params.instruct,
                    language=params.resolved_language,
                )
            else:  # base / voice cloning
                xvec = params.ref_text is None or params.ref_text == ""
                audio_list, sr = model.generate_voice_clone(
                    text,
                    language=params.resolved_language,
                    ref_audio=ref_audio_data,
                    ref_text=params.ref_text,
                    x_vector_only_mode=xvec,
                )

            # Extract the first segment (or only segment since splitting is removed)
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

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Temporary save for Sox
        temp_path = Path(output_path).with_suffix(".tmp.wav")
        AudioUtils.save_waveform(waveform, sr, str(temp_path))

        # Post-Processing
        if not SoxAudioProcessor.apply_effects(str(temp_path), output_path):
            # Fallback if Sox fails or is missing
            if temp_path.exists():
                temp_path.replace(output_path)
        elif temp_path.exists():
            temp_path.unlink()

        logger.info(f"Audio saved to {output_path}")
        return output_path

    def generate_audio_stream(
        self, text: str, params: TTSParams = None, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Generates audio and yields it in chunks."""
        logger.info("Starting audio stream generation...")
        waveform, sr = self.generate_audio(text, params)

        # Convert to int16 for playback (standard for streaming)
        audio_np = waveform.squeeze().cpu().numpy()
        audio_int16 = (audio_np * 32767).astype(np.int16)

        # We can yield a WAV header first or just raw PCM.
        # For simplicity and "real-time" feeling, raw PCM is common.
        # But some players expect WAV. Let's provide a raw stream.

        # If we want a valid WAV stream, we'd need to yield the header once.
        # Let's just yield the raw bytes of the int16 data.
        audio_bytes = audio_int16.tobytes()

        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i : i + chunk_size]

    def _get_reference_audio(self, params: TTSParams) -> tuple | None:
        """Helper to load reference audio."""
        # Skip if reference_audio is empty, None, or the Swagger placeholder 'string'
        if not params.reference_audio or params.reference_audio == "string":
            # Load default if base mode
            if params.mode == "base":
                voices = list(self.settings.VOICES_DIR.glob("*.wav"))
                if voices:
                    logger.info(f"Using default reference audio: {voices[0].name}")
                    data, sr = sf.read(str(voices[0]))
                    return (data, sr)
                logger.error(
                    f"Base mode requires reference audio. "
                    f"No .wav files found in {self.settings.VOICES_DIR.absolute()}"
                )
            return None

        ref_path = self.settings.VOICES_DIR / params.reference_audio
        if ref_path.exists():
            logger.info(f"Using reference audio: {ref_path.name}")
            data, sr = sf.read(str(ref_path))
            return (data, sr)

        logger.warning(f"Reference audio not found: {ref_path}")
        return None
