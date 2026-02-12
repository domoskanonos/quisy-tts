"""Qwen3-TTS engine implementation using vLLM backend."""

import re
import time
from collections.abc import Generator
from pathlib import Path

import numpy as np
import torch
from vllm import LLM, SamplingParams

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


class QwenVLLMBackend:
    """High-performance vLLM-based backend for Qwen3-TTS."""

    def __init__(self, settings: ProjectSettings) -> None:
        """Initialize the vLLM backend."""
        self.settings = settings

        # Initialize model
        self.model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        self.llm = LLM(
            model=self.model_name,
            gpu_memory_utilization=0.9,
            dtype="bfloat16",
        )

        # Official Qwen3-TTS recommended sampling parameters
        self.sampling_params = SamplingParams(
            temperature=QWEN_GENERATION_CONFIG["temperature"],
            top_p=QWEN_GENERATION_CONFIG["top_p"],
            top_k=int(QWEN_GENERATION_CONFIG["top_k"]),
            max_tokens=int(QWEN_GENERATION_CONFIG["max_new_tokens"]),
            repetition_penalty=QWEN_GENERATION_CONFIG["repetition_penalty"],
            detokenize=False,
        )

    def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio using vLLM engine."""
        inputs = self._prepare_inputs(text, params)

        # vLLM generate returns a list of RequestOutput
        outputs = self.llm.generate([inputs], self.sampling_params)  # type: ignore

        final_audio: torch.Tensor | None = None
        sr: int = 24000  # default fallback

        for output in outputs:
            # Qwen3-TTS integration in vLLM standardizes output format
            # Trying to inspect available fields on the output object
            if hasattr(output, "multimodal_output") and output.multimodal_output:
                if "audio" in output.multimodal_output:
                    audio_tensor = output.multimodal_output["audio"]
                    sr = output.multimodal_output["sr"].item()
                    final_audio = audio_tensor.float().detach().cpu()

        if final_audio is None:
            # Fallback if standard multimodal output isn't populated as expected
            # This might require adjustment based on exact vLLM version behavior
            logger.warning("No audio found in multimodal_output, checking text/token output")
            pass

        if final_audio is None:
            raise ValueError("vLLM generation produced no audio output")

        # Ensure 2D [1, T] shape
        if final_audio.ndim == 1:
            final_audio = final_audio.unsqueeze(0)

        return final_audio, sr

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

    def _prepare_inputs(self, text: str, params: TTSParams) -> dict:
        """Prepare input dictionary for vLLM-Omni."""
        task_type = "Base"
        if params.mode == "voice_design":
            task_type = "VoiceDesign"
        elif params.mode == "custom_voice":
            task_type = "CustomVoice"

        prompt = f"<|im_start|>assistant\n{text}<|im_end|>\n<|im_start|>assistant\n"

        additional_info: dict = {
            "task_type": [task_type],
            "text": [text],
            "language": [params.resolved_language],
            "max_new_tokens": [QWEN_GENERATION_CONFIG["max_new_tokens"]],
        }

        if params.mode == "base":
            ref_audio_path = self._resolve_ref_audio(params)
            if ref_audio_path:
                additional_info["ref_audio"] = [ref_audio_path]
                additional_info["ref_text"] = [params.ref_text or ""]

        if params.instruct:
            additional_info["instruct"] = [params.instruct]

        return {"prompt": prompt, "additional_information": additional_info}

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
    """Qwen3-TTS implementation using vLLM backend."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine with vLLM."""
        self.settings = ProjectConfig.get_settings()
        logger.info("Initializing vLLM backend...")
        self.backend = QwenVLLMBackend(self.settings)
        logger.info("vLLM backend initialized successfully.")

    def generate_audio(self, text: str, params: TTSParams | None = None) -> tuple[torch.Tensor, int]:
        """Generates audio waveform via vLLM backend."""
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
        """Stream audio via vLLM backend."""
        if params is None:
            params = TTSParams()

        logger.info("Starting audio stream generation...")
        yield from self.backend.generate_audio_stream(text, params, chunk_size)
