"""Qwen3-TTS engine implementation using the official qwen-tts package."""

import asyncio
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import numpy as np
import torch
from qwen_tts import Qwen3TTSModel

from audio.processor import AudioUtils
from config import ProjectConfig, ProjectSettings
from core import TTSEngine
from schemas import TTSParams
from services.text_splitter import get_text_splitter

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

# Model mapping: each generation mode requires a dedicated model
MODEL_MAP = {
    "base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "custom_voice": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
}

# Silence duration between chunks in seconds
INTER_CHUNK_SILENCE_SECS = 0.15


class QwenTTSBackend:
    """Backend for Qwen3-TTS using the official qwen-tts package with lazy async loading."""

    def __init__(self, settings: ProjectSettings) -> None:
        """Initialize backend without loading any models."""
        self.settings = settings
        self._models: dict[str, Qwen3TTSModel] = {}
        self._locks: dict[str, asyncio.Lock] = {mode: asyncio.Lock() for mode in MODEL_MAP}
        self._text_splitter = get_text_splitter()

    async def ensure_loaded(self, mode: str = "base") -> Qwen3TTSModel:
        """Ensure the model for a given mode is loaded. Safe to call concurrently.

        Args:
            mode: Generation mode (base, voice_design, custom_voice).

        Returns:
            The loaded Qwen3TTSModel for the requested mode.
        """
        if mode in self._models:
            return self._models[mode]

        lock = self._locks.get(mode)
        if lock is None:
            raise ValueError(f"Unknown mode: {mode}. Available: {list(MODEL_MAP.keys())}")

        async with lock:
            # Double-check after acquiring lock
            if mode in self._models:
                return self._models[mode]

            model_name = MODEL_MAP[mode]
            logger.info(f"Loading Qwen3-TTS model for mode '{mode}': {model_name}...")
            start_time = time.time()

            # Run blocking model load in thread pool
            loop = asyncio.get_running_loop()
            model = await loop.run_in_executor(None, self._load_model_sync, model_name)
            self._models[mode] = model

            elapsed = time.time() - start_time
            logger.info(f"Qwen3-TTS model '{mode}' loaded successfully in {elapsed:.2f}s")
            return model

    def _load_model_sync(self, model_name: str) -> Qwen3TTSModel:
        """Synchronous model loading (runs in thread)."""
        return Qwen3TTSModel.from_pretrained(
            model_name,
            device_map="auto",
            dtype=torch.bfloat16,
        )

    async def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio using qwen-tts (async).

        For long texts, splits into chunks using spaCy, generates audio for each,
        and concatenates them with short silence gaps for natural pacing.
        """
        model = await self.ensure_loaded(params.mode)

        # Split text into chunks using language-aware splitter
        language = params.resolved_language if hasattr(params, "resolved_language") else (params.language or "german")
        chunks = self._text_splitter.split(text, language)

        if len(chunks) <= 1:
            # Short text — generate directly (no splitting overhead)
            return await self._generate_single(model, text, params)

        logger.info(f"Text split into {len(chunks)} chunks for language '{language}' (total {len(text)} chars)")

        # Generate audio for each chunk
        audio_segments: list[torch.Tensor] = []
        sample_rate = 24000  # Will be overwritten by actual SR

        for i, chunk in enumerate(chunks):
            logger.debug(f"Generating chunk {i + 1}/{len(chunks)}: {chunk[:60]}...")
            waveform, sr = await self._generate_single(model, chunk, params)
            audio_segments.append(waveform)
            sample_rate = sr

        # Concatenate with silence gaps
        silence_samples = int(sample_rate * INTER_CHUNK_SILENCE_SECS)
        silence = torch.zeros(1, silence_samples)

        combined_parts: list[torch.Tensor] = []
        for i, segment in enumerate(audio_segments):
            combined_parts.append(segment)
            if i < len(audio_segments) - 1:
                combined_parts.append(silence)

        final_audio = torch.cat(combined_parts, dim=1)
        logger.info(
            f"Combined {len(audio_segments)} audio chunks. Total duration: {final_audio.shape[1] / sample_rate:.1f}s"
        )

        return final_audio, sample_rate

    async def _generate_single(self, model: Qwen3TTSModel, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio for a single text chunk."""
        gen_kwargs = {
            "max_new_tokens": QWEN_GENERATION_CONFIG["max_new_tokens"],
            "temperature": QWEN_GENERATION_CONFIG["temperature"],
            "top_p": QWEN_GENERATION_CONFIG["top_p"],
            "top_k": QWEN_GENERATION_CONFIG["top_k"],
            "repetition_penalty": QWEN_GENERATION_CONFIG["repetition_penalty"],
        }

        loop = asyncio.get_running_loop()
        wavs, sr = await loop.run_in_executor(
            None,
            lambda: self._generate_sync(model, text, params, gen_kwargs),
        )

        audio_np = wavs[0]
        audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)  # [1, T]
        return audio_tensor, sr

    def _generate_sync(self, model: Qwen3TTSModel, text: str, params: TTSParams, gen_kwargs: dict) -> tuple[list, int]:
        """Synchronous generation logic."""
        if params.mode == "voice_design":
            return model.generate_voice_design(
                text=text,
                language=params.resolved_language,
                instruct=params.instruct or "",
                **gen_kwargs,
            )
        elif params.mode == "custom_voice":
            return model.generate_custom_voice(
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
            return model.generate_voice_clone(
                text=text,
                language=params.resolved_language,
                ref_audio=ref_audio_path,
                ref_text=params.ref_text or "",
                **gen_kwargs,
            )

    async def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio by splitting text into sentences using spaCy (async)."""
        await self.ensure_loaded(params.mode)

        # Use language-aware text splitting
        language = params.resolved_language if hasattr(params, "resolved_language") else (params.language or "german")
        chunks = self._text_splitter.split(text, language)

        for chunk in chunks:
            if not chunk:
                continue

            # Generate audio for each chunk
            waveform, _ = await self.generate_audio(chunk, params)

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

            # If a specific file was requested but not found, RAISE ERROR instead of falling back
            from core.exceptions import ReferenceAudioNotFoundError

            raise ReferenceAudioNotFoundError(
                f"Requested reference audio '{params.reference_audio}' not found in voices directory."
            )

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
    """Qwen3-TTS implementation using the official qwen-tts package (Async).

    Loads separate models per generation mode (base, voice_design, custom_voice)
    lazily on first use.
    """

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()
        logger.info("Initializing Qwen3-TTS backend (Lazy, multi-model)...")
        self.backend = QwenTTSBackend(self.settings)

    async def ensure_loaded(self, mode: str = "base") -> None:
        """Explicitly trigger model loading for a specific mode."""
        await self.backend.ensure_loaded(mode)

    async def generate_audio(self, text: str, params: TTSParams | None = None) -> tuple[torch.Tensor, int]:
        """Generates audio waveform via qwen-tts backend (async)."""
        if params is None:
            params = TTSParams()

        logger.info(
            f"Starting audio generation | Mode: {params.mode} | Text Length: {len(text)} | Language: {params.language}"
        )
        total_start_time = time.time()

        final_audio, sr = await self.backend.generate_audio(text, params)

        logger.info(f"Audio generation successful. Total time: {time.time() - total_start_time:.4f}s")
        return final_audio, sr

    async def generate_and_save(self, text: str, output_path: str, params: TTSParams | None = None) -> str:
        """Generates audio and saves it to a file (async)."""
        if params is None:
            params = TTSParams()

        waveform, sr = await self.generate_audio(text, params)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # File I/O in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, AudioUtils.save_waveform, waveform, sr, output_path)

        logger.info(f"Audio saved to {output_path}")
        return output_path

    async def generate_audio_stream(
        self, text: str, params: TTSParams | None = None, chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio via qwen-tts backend (async)."""
        if params is None:
            params = TTSParams()

        logger.info("Starting audio stream generation...")
        async for chunk in self.backend.generate_audio_stream(text, params, chunk_size):
            yield chunk
