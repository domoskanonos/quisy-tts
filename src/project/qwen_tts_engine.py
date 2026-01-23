from pathlib import Path

import soundfile as sf
import torch

from project.audio.processor import AudioUtils, SoxAudioProcessor
from project.config import ProjectConfig
from project.models.manager import ModelManager
from project.schemas import TTSParams
from project.text.optimizer import NaturalOptimizer


logger = ProjectConfig.get_logger()


class QwenTextToSpeech:
    """Orchestrates TTS generation using modular components."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()
        self.optimizer = NaturalOptimizer()

    def generate_audio(
        self, text: str, params: TTSParams = None
    ) -> tuple[torch.Tensor, int]:
        """Generates audio bytes for the given text and parameters."""
        if params is None:
            params = TTSParams()

        # 1. Optimize Text
        clean_text = self.optimizer.optimize(text)
        logger.info(
            f"Generating audio for: '{clean_text[:50]}...' in mode '{params.mode}'"
        )

        # 2. Get Model
        model = ModelManager.get_model(mode=params.mode, size=params.model_size)

        # 3. Load Reference Audio (if needed)
        ref_audio_data = self._get_reference_audio(params)

        # 4. Generate
        try:
            if params.mode == "voice_design":
                audio_list, sr = model.generate_voice_design(
                    clean_text, instruct=params.instruct, language=params.language_id
                )
            elif params.mode == "custom_voice":
                audio_list, sr = model.generate_custom_voice(
                    clean_text,
                    speaker=params.speaker,
                    instruct=params.instruct,
                    language=params.language_id,
                )
            else:  # base / voice cloning
                xvec = params.ref_text is None or params.ref_text == ""
                audio_list, sr = model.generate_voice_clone(
                    clean_text,
                    language=params.language_id,
                    ref_audio=ref_audio_data,
                    ref_text=params.ref_text,
                    x_vector_only_mode=xvec,
                )

            # Extract the first segment (or only segment since splitting is removed)
            if not audio_list:
                raise ValueError("Model returned empty audio list")

            final_audio = torch.from_numpy(audio_list[0]).unsqueeze(0)

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

    def _get_reference_audio(self, params: TTSParams) -> tuple | None:
        """Helper to load reference audio."""
        if not params.reference_audio:
            # Load default if base mode
            if params.mode == "base":
                voices = list(Path(self.settings.VOICES_DIR).glob("*.wav"))
                if voices:
                    data, sr = sf.read(str(voices[0]))
                    return (data, sr)
            return None

        ref_path = Path(self.settings.VOICES_DIR) / params.reference_audio
        if ref_path.exists():
            data, sr = sf.read(str(ref_path))
            return (data, sr)

        logger.warning(f"Reference audio not found: {ref_path}")
        return None
