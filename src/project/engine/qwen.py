"""Qwen3-TTS engine implementation."""

import re
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch

from project.audio.processor import AudioUtils, SoxAudioProcessor
from project.config import ProjectConfig
from project.core import TTSEngine
from project.engine.backend_interface import TTSBackend
from project.models.manager import ModelManager
from project.schemas import TTSParams


# Optional vLLM import
try:
    import vllm  # noqa: F401

    VLLM_AVAILABLE = True
    # We don't log here yet as logger is not initialized
except ImportError:
    VLLM_AVAILABLE = False


logger = ProjectConfig.get_logger()

if VLLM_AVAILABLE:
    logger.info("vLLM package is installed.")
else:
    logger.info("vLLM package not found.")


class QwenTransformersBackend:
    """Standard Transformers-based backend (Windows compatible)."""

    def __init__(self, settings: Any) -> None:
        """Initialize the transformers backend."""
        self.settings = settings
        # Use model defaults (greedy decoding) for stable, deterministic output
        # max_new_tokens: 8192 prevents infinite generation on short texts
        self.default_gen_kwargs: dict = {"max_new_tokens": 8192}

        # Cache for voice clone prompts (keyed by ref_audio + ref_text hash)
        # Note: We removed caching logic in previous steps, but keeping structure clean.
        self._voice_prompts: dict[str, object] = {}

    def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio using standard transformers model."""
        model = ModelManager.get_model(mode=params.mode, size=params.model_size)
        ref_audio_data = self._get_reference_audio(params)

        gen_kwargs = self.default_gen_kwargs

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
            voice_prompt = self._create_voice_prompt(
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

        return torch.from_numpy(audio_list[0]).unsqueeze(0), sr

    def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Simulate streaming by chunking text."""
        # Simple sentence splitting for now
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

    def _get_reference_audio(self, params: TTSParams) -> tuple | None:
        """Helper to load reference audio."""
        if not params.reference_audio:
            if params.mode == "base":
                default_ref = self.settings.DEFAULT_REFERENCE_AUDIO
                if default_ref:
                    ref_path = self.settings.VOICES_DIR / default_ref
                    if ref_path.exists():
                        return _load_audio(str(ref_path))

                voices = list(self.settings.VOICES_DIR.glob("*.wav"))
                if voices:
                    return _load_audio(str(voices[0]))
            return None

        ref_path = self.settings.VOICES_DIR / params.reference_audio
        if ref_path.exists():
            return _load_audio(str(ref_path))
        return None

    def _create_voice_prompt(
        self,
        model: Any,
        ref_audio: tuple | None,
        ref_text: str | None,
        x_vector_only: bool,
    ) -> object:
        """Create a voice clone prompt."""
        if ref_audio is None:
            return None
        try:
            return model.create_voice_clone_prompt(
                ref_audio=ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only,
            )
        except Exception as e:
            logger.warning(f"Failed to create voice prompt: {e}")
            return None


class QwenVLLMBackend:
    """High-performance vLLM-based backend (Linux/WSL only)."""

    def __init__(self, settings: Any) -> None:
        """Initialize the vLLM backend."""
        self.settings = settings
        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM not available. Install 'vllm' package.")

        # We need to defer imports to avoid runtime errors on Windows
        from vllm import Omni, SamplingParams  # type: ignore # noqa: PLC0415

        # Initialize model (lazy loading mostly handled by vLLM)
        # Note: vLLM loads model on first use or explicit init
        # Simplified handling: Base model handles all modes
        self.model_name = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        self.omni = Omni(
            model=self.model_name,
            gpu_memory_utilization=0.9,  # Adjust based on Docker setup
            dtype="bfloat16",
        )

        self.sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.9,
            max_tokens=8192,
            detokenize=False,
            repetition_penalty=1.1,  # Recommended for long text
        )

    def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio using vLLM engine."""
        inputs = self._prepare_inputs(text, params)

        # vLLM generate returns an iterator
        # We consume it all for "generate_audio" (non-streaming)
        # Note: vllm-omni generates multimodal output

        # Wrap inputs in list for batch (size 1)
        omni_generator = self.omni.generate([inputs], [self.sampling_params])

        final_audio: torch.Tensor | None = None
        sr: int = 24000  # default fallback

        for stage_outputs in omni_generator:
            for output in stage_outputs.request_output:
                if "audio" in output.multimodal_output:
                    audio_tensor = output.multimodal_output["audio"]
                    sr = output.multimodal_output["sr"].item()
                    final_audio = audio_tensor.float().detach().cpu()

        if final_audio is None:
            raise ValueError("vLLM generation produced no audio output")

        # Ensure 2D [1, T] shape
        if final_audio.ndim == 1:
            final_audio = final_audio.unsqueeze(0)

        return final_audio, sr

    def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Stream audio (Simulated or Real).

        Note: Currently vLLM-Omni only supports offline inference properly.
        Real streaming requires a different 'Online Serving' setup.
        For now, we use the same sentence-split trick as Transformers backend
        to provide a responsive UX.
        """
        # Fallback to sentence splitting logic to mimic streaming
        # Can be replaced with real vLLM streaming when available

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
        # Mapping logic based on params.mode

        task_type = "Base"
        if params.mode == "voice_design":
            task_type = "VoiceDesign"  # Requires VoiceDesign model
        elif params.mode == "custom_voice":
            task_type = "CustomVoice"  # Requires CustomVoice model

        # Simplified prompt construction (based on end2end.py)
        prompt = f"<|im_start|>assistant\n{text}<|im_end|>\n<|im_start|>assistant\n"

        additional_info = {
            "task_type": [task_type],
            "text": [text],
            "language": [params.resolved_language],
            "max_new_tokens": [8192],
        }

        if params.mode == "base":
            ref_audio_path = self._resolve_ref_audio(params)
            if ref_audio_path:
                additional_info["ref_audio"] = [ref_audio_path]
                additional_info["ref_text"] = [params.ref_text or ""]
                # x_vector_only logic could be added here

        if params.instruct:
            additional_info["instruct"] = [params.instruct]

        return {"prompt": prompt, "additional_information": additional_info}

    def _resolve_ref_audio(self, params: TTSParams) -> str | None:
        """Resolve reference audio path for vLLM."""
        if params.reference_audio:
            path = self.settings.VOICES_DIR / params.reference_audio
            if path.exists():
                return str(path)

        # Fallback logic similar to transformers backend...
        default = self.settings.DEFAULT_REFERENCE_AUDIO
        if default:
            path = self.settings.VOICES_DIR / default
            if path.exists():
                return str(path)

        voices = list(self.settings.VOICES_DIR.glob("*.wav"))
        if voices:
            return str(voices[0])

        return None


logger = ProjectConfig.get_logger()


def _load_audio(path: str) -> tuple:
    """Load audio file from disk (no caching)."""
    start_time = time.time()
    if logger.isEnabledFor(10):
        logger.debug("Loading audio file: %s", path)
    data, sr = sf.read(path)
    if logger.isEnabledFor(10):
        logger.debug("Loaded audio file in %.4fs", time.time() - start_time)
    return (data, sr)


class QwenTextToSpeech(TTSEngine):
    """Qwen3-TTS implementation delegating to appropriate backend."""

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()

        # Select backend
        # For now, default to transformers until we implement the full VLLM class
        # Ideally check env var or VLLM_AVAILABLE
        self.backend: TTSBackend = QwenTransformersBackend(self.settings)

        if VLLM_AVAILABLE:
            try:
                logger.info("Initializing vLLM backend...")
                self.backend: TTSBackend = QwenVLLMBackend(self.settings)
                logger.info("vLLM backend initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize vLLM backend: {e}. Falling back.")
                self.backend: TTSBackend = QwenTransformersBackend(self.settings)
        else:
            logger.info("vLLM not detected - using Transformers backend")

    def generate_audio(
        self, text: str, params: TTSParams | None = None
    ) -> tuple[torch.Tensor, int]:
        """Generates audio waveform via backend."""
        if params is None:
            params = TTSParams()

        logger.info(
            f"Starting audio generation | Mode: {params.mode} | "
            f"Text Length: {len(text)} | Language: {params.language}"
        )
        total_start_time = time.time()

        final_audio, sr = self.backend.generate_audio(text, params)

        logger.info(
            f"Audio generation successful. "
            f"Total time: {time.time() - total_start_time:.4f}s"
        )
        return final_audio, sr

    def generate_and_save(
        self, text: str, output_path: str, params: TTSParams | None = None
    ) -> str:
        """Generates audio and saves it to a file with post-processing."""
        if params is None:
            params = TTSParams()

        waveform, sr = self.generate_audio(text, params)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        temp_path = Path(output_path).with_suffix(".tmp.wav")
        AudioUtils.save_waveform(waveform, sr, str(temp_path))

        if SoxAudioProcessor.apply_effects(str(temp_path), output_path):
            if temp_path.exists():
                temp_path.unlink()
        elif temp_path.exists():
            if Path(output_path).exists():
                Path(output_path).unlink()
            temp_path.replace(output_path)

        logger.info(f"Audio saved to {output_path}")
        return output_path

    def generate_audio_stream(
        self, text: str, params: TTSParams | None = None, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Stream audio via backend."""
        if params is None:
            params = TTSParams()

        logger.info("Starting audio stream generation...")
        yield from self.backend.generate_audio_stream(text, params, chunk_size)
