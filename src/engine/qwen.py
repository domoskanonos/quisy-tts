"""Qwen3-TTS engine implementation using the official qwen-tts package."""

import re
import time
from collections.abc import Generator
from pathlib import Path

import numpy as np
import torch
from qwen_tts import Qwen3TTSModel

from audio.processor import AudioUtils
from config import ProjectConfig, ProjectSettings
from core import TTSEngine
from schemas import TTSParams

logger = ProjectConfig.get_logger()


# Centralized generation config for consistency
# Source: https://github.com/QwenLM/Qwen3-TTS/blob/main/examples/test_model_12hz_base.py
QWEN_GENERATION_CONFIG = {
    "temperature": 0.9,
    "top_p": 1.0,
    "top_k": 50,
    "repetition_penalty": 1.05,
    "max_new_tokens": 2048,
}


class QwenTTSBackend:
    """Backend for Qwen3-TTS using the official qwen-tts package."""

    def __init__(self, settings: ProjectSettings) -> None:
        """Initialize the qwen-tts backend."""
        self.settings = settings

        # Initialize model
        self.model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        logger.info(f"Loading Qwen3-TTS model: {self.model_name}")
        self.model = Qwen3TTSModel.from_pretrained(
            self.model_name,
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )
        logger.info("Qwen3-TTS model loaded successfully.")

    def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio using qwen-tts."""
        gen_kwargs = {
            "max_new_tokens": QWEN_GENERATION_CONFIG["max_new_tokens"],
            "temperature": QWEN_GENERATION_CONFIG["temperature"],
            "top_p": QWEN_GENERATION_CONFIG["top_p"],
            "top_k": QWEN_GENERATION_CONFIG["top_k"],
            "repetition_penalty": QWEN_GENERATION_CONFIG["repetition_penalty"],
        }

        if params.mode == "voice_design":
            wavs, sr = self.model.generate_voice_design(
                text=text,
                language=params.resolved_language,
                instruct=params.instruct or "",
                **gen_kwargs,
            )
        elif params.mode == "custom_voice":
            wavs, sr = self.model.generate_custom_voice(
                text=text,
                language=params.resolved_language,
                speaker=params.speaker or "Vivian",
                instruct=params.instruct or "",
                **gen_kwargs,
            )
        else:
            # Base mode = voice clone
            ref_audio_path = self._resolve_ref_audio(params)
            if not ref_audio_path:
                from core.exceptions import ReferenceAudioNotFoundError

                raise ReferenceAudioNotFoundError(
                    "No reference audio found for voice cloning. "
                    "Please provide `reference_audio` or ensure a default voice exists in `voices/`."
                )
            wavs, sr = self.model.generate_voice_clone(
                text=text,
                language=params.resolved_language,
                ref_audio=ref_audio_path,
                ref_text=params.ref_text or "",
                **gen_kwargs,
            )

        # wavs is a list of numpy arrays, take the first one
        audio_np = wavs[0]
        audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)  # [1, T]

        return audio_tensor, sr

    def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Stream audio by splitting text into sentences."""
        sentences = re.split(r"([.!?]+)", text)
        chunks = []
        current_chunk = ""
        for item in sentences:
            current_chunk += item
            if re.match(r"[.!?]+", item):
                chunks.append(current_chunk.strip())
                current_chunk = ""
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        for chunk in chunks:
            if not chunk:
                continue
            waveform, _ = self.generate_audio(chunk, params)
            audio_np = waveform.squeeze().cpu().numpy()
            audio_int16 = (audio_np * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            for k in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[k : k + chunk_size]

    def _resolve_ref_audio(self, params: TTSParams) -> str | None:
        """Resolve reference audio path."""
        if params.reference_audio:
            path = self.settings.VOICES_DIR / params.reference_audio
            if path.exists():
                return str(path)

        default = self.settings.DEFAULT_REFERENCE_AUDIO
        if default:
            path = self.settings.VOICES_DIR / default
            if path.exists():
                return str(path)

        voices = list(self.settings.VOICES_DIR.glob("*.wav"))
        if voices:
            return str(voices[0])

        return None


class QwenTextToSpeech(TTSEngine):
    """Qwen3-TTS implementation using the official qwen-tts package."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()
        logger.info("Initializing Qwen3-TTS backend...")
        self.backend = QwenTTSBackend(self.settings)
        logger.info("Qwen3-TTS backend initialized successfully.")

    def generate_audio(self, text: str, params: TTSParams | None = None) -> tuple[torch.Tensor, int]:
        """Generates audio waveform via qwen-tts backend."""
        if params is None:
            params = TTSParams()

        logger.info(
            f"Starting audio generation | Mode: {params.mode} | Text Length: {len(text)} | Language: {params.language}"
        )
        total_start_time = time.time()

        final_audio, sr = self.backend.generate_audio(text, params)

        logger.info(f"Audio generation successful. Total time: {time.time() - total_start_time:.4f}s")
        return final_audio, sr

    def generate_and_save(self, text: str, output_path: str, params: TTSParams | None = None) -> str:
        """Generates audio and saves it to a file."""
        if params is None:
            params = TTSParams()

        waveform, sr = self.generate_audio(text, params)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save directly without post-processing (per Qwen3-TTS best practice)
        AudioUtils.save_waveform(waveform, sr, output_path)

        logger.info(f"Audio saved to {output_path}")
        return output_path

    def generate_audio_stream(
        self, text: str, params: TTSParams | None = None, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Stream audio via qwen-tts backend."""
        if params is None:
            params = TTSParams()

        logger.info("Starting audio stream generation...")
        yield from self.backend.generate_audio_stream(text, params, chunk_size)
