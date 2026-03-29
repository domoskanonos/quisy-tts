"""Qwen3-TTS engine implementation using the official qwen-tts package."""

import asyncio
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import numpy as np
from typing import Any
from qwen_tts import Qwen3TTSModel

from audio.processor import AudioUtils
from config import ProjectConfig, ProjectSettings
from core import TTSEngine
from schemas import TTSParams
from services.text_splitter import get_text_splitter
from schemas.languages import resolve_language

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
        """Ensure the model for a given mode is loaded. Safe to call concurrently."""
        logger.info(f"Debug: ensure_loaded called for mode: {mode}")
        if mode in self._models:
            logger.info(f"Debug: mode {mode} already loaded")
            return self._models[mode]

        lock = self._locks.get(mode)
        if lock is None:
            raise ValueError(f"Unknown mode: {mode}. Available: {list(MODEL_MAP.keys())}")

        logger.info(f"Debug: acquiring lock for mode: {mode}")
        async with lock:
            # Double-check after acquiring lock
            if mode in self._models:
                return self._models[mode]

            model_name = MODEL_MAP[mode]
            logger.info(f"Loading Qwen3-TTS model for mode '{mode}': {model_name}...")
            start_time = time.time()

            # Run blocking model load in thread pool
            loop = asyncio.get_running_loop()
            logger.info("Debug: calling run_in_executor for _load_model_sync")
            model = await loop.run_in_executor(None, self._load_model_sync, model_name)
            logger.info("Debug: run_in_executor finished")
            self._models[mode] = model

            elapsed = time.time() - start_time
            logger.info(f"Qwen3-TTS model '{mode}' loaded successfully in {elapsed:.2f}s")
            return model

    def _load_model_sync(self, model_name: str) -> Qwen3TTSModel:
        """Synchronous model loading (runs in thread)."""
        # Import torch lazily to allow tests/environments without torch installed
        try:
            import torch as _torch

            torch = _torch
        except ImportError:
            torch = None

        kwargs: dict[str, Any] = {"device_map": "auto", "attn_implementation": "sdpa"}
        if torch is not None:
            # Set dtype only if torch exposes the attribute
            dtype = getattr(torch, "bfloat16", None)
            if dtype is not None:
                kwargs["dtype"] = dtype

        return Qwen3TTSModel.from_pretrained(model_name, **kwargs)

    async def generate_audio(self, text: str, params: TTSParams) -> tuple[Any, int]:
        """Generate audio using qwen-tts (async).

        For long texts, splits into chunks using spaCy, generates audio for each,
        and concatenates them with short silence gaps for natural pacing.
        """
        model = await self.ensure_loaded(params.mode)

        # The engine expects a single chunk of text and generates it.
        # Splitting and orchestration are handled by the TTSService to avoid duplicate work.
        return await self._generate_single(model, text, params)

    async def _generate_single(self, model: Qwen3TTSModel, text: str, params: TTSParams) -> tuple[Any, int]:
        """Generate audio for a single text chunk."""
        gen_kwargs = {
            "max_new_tokens": QWEN_GENERATION_CONFIG["max_new_tokens"],
            "temperature": QWEN_GENERATION_CONFIG["temperature"],
            "top_p": QWEN_GENERATION_CONFIG["top_p"],
            "top_k": QWEN_GENERATION_CONFIG["top_k"],
            "repetition_penalty": QWEN_GENERATION_CONFIG["repetition_penalty"],
        }

        # Defensive: ensure resolved_language is canonical and log it
        # Ensure language is provided and resolved; do not silently fall back.
        try:
            if not params.language:
                raise ValueError("language must be provided in TTSParams for generation")
            resolved_lang = (
                params.resolved_language
                if hasattr(params, "resolved_language") and params.resolved_language
                else resolve_language(params.language)
            )
        except Exception as e:
            raise ValueError("language must be provided in TTSParams for generation") from e
        logger.debug(f"_generate_single: resolved_language={resolved_lang}, mode={params.mode}")

        loop = asyncio.get_running_loop()
        wavs, sr = await loop.run_in_executor(
            None,
            lambda: self._generate_sync(model, text, params, gen_kwargs),
        )

        # Convert numpy array to torch tensor if torch is available, otherwise return numpy
        audio_np = wavs[0]
        # Log the raw waveform shape for debugging short/empty outputs
        try:
            logger.debug(
                "Raw generated audio shape: %s, sample_rate=%s", getattr(audio_np, "shape", type(audio_np)), sr
            )
        except Exception:
            logger.debug("Raw generated audio shape unavailable")

        try:
            import torch

            audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)  # [1, T]
            logger.debug("Converted generated audio to torch tensor with shape: %s", tuple(audio_tensor.shape))
            return audio_tensor, sr
        except Exception:
            logger.debug("Torch not available or conversion failed; returning numpy array")
            return audio_np, sr

    def _generate_sync(self, model: Qwen3TTSModel, text: str, params: TTSParams, gen_kwargs: dict) -> tuple[list, int]:
        """Synchronous generation logic."""
        logger.info("Generation started")
        start = time.time()
        try:
            if params.mode == "voice_design":
                logger.info("Calling model.generate_voice_design...")
                result = model.generate_voice_design(
                    text=text,
                    language=params.resolved_language,
                    instruct=params.instruct or "",
                    **gen_kwargs,
                )
                logger.info("model.generate_voice_design finished.")
            else:
                # Base mode = voice clone
                ref_audio_path = self._resolve_ref_audio(params)
                if not ref_audio_path:
                    from core.exceptions import ReferenceAudioNotFoundError

                    raise ReferenceAudioNotFoundError(
                        "No reference audio found for voice cloning. "
                        "Please provide `reference_audio` or ensure a default voice exists in `voices/`."
                    )
                result = model.generate_voice_clone(
                    text=text,
                    language=params.resolved_language,
                    ref_audio=ref_audio_path,
                    ref_text=params.ref_text or "",
                    **gen_kwargs,
                )

            elapsed = time.time() - start
            logger.info(f"Generation finished in {elapsed:.3f}s")

            # result expected: (wavs, sr)
            try:
                wavs, sr = result
                # Log model type and returned waveform details to help detect stub usage
                logger.debug("Model type during generation: %s", type(model))
                logger.debug(
                    "Generation finished in %.3fs; returned %d waveform(s); sample_rate=%s", elapsed, len(wavs), sr
                )
                # Log shape of first waveform if possible
                try:
                    logger.debug("First waveform shape: %s", getattr(wavs[0], "shape", type(wavs[0])))
                except Exception:
                    logger.debug("Could not determine waveform shape")
            except Exception:
                # Fall back if model returns something unexpected
                logger.debug("Generation finished in %.3fs; result type: %s", elapsed, type(result))
            return result
        except Exception:
            # Re-raise after logging to preserve original behavior
            logger.exception("Error during synchronous generation call")
            raise

    async def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio by generating a single text chunk and yielding bytes.

        Note: orchestration and splitting are handled by the TTSService; the engine
        stream method simply delegates to generate_audio for a single chunk and
        yields bytes. The TTSService stream path handles multiple chunks.
        """
        await self.ensure_loaded(params.mode)

        waveform, _ = await self._generate_single(await self.ensure_loaded(params.mode), text, params)

        audio_np = waveform.squeeze().cpu().numpy()
        audio_int16 = (audio_np * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        for k in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[k : k + chunk_size]

    def _resolve_ref_audio(self, params: TTSParams) -> str | None:
        """Resolve reference audio path."""
        if params.reference_audio:
            # Accept only a voice ID. Do NOT accept a filename here.
            from services.voice_service import VoiceService
            from core.exceptions import ReferenceAudioNotFoundError

            try:
                vs = VoiceService(self.settings.VOICES_DIR)
                voice = vs.get_voice(params.reference_audio)
                if not voice:
                    raise ReferenceAudioNotFoundError(
                        f"Requested reference voice id '{params.reference_audio}' not found in database."
                    )

                # Reference audio is always voice_{voice_id}.wav
                path = self.settings.VOICES_DIR / f"voice_{params.reference_audio}.wav"
                if not path.exists():
                    raise ReferenceAudioNotFoundError(
                        f"Audio file for voice '{params.reference_audio}' not found at: {path}"
                    )

                return str(path)
            except ReferenceAudioNotFoundError:
                raise
            except Exception:
                # Unexpected DB error -> surface as not found
                raise ReferenceAudioNotFoundError(f"Failed to resolve reference voice id '{params.reference_audio}'.")

        # Resolve default by DEFAULT_VOICE_ID if present
        default_voice_id = getattr(self.settings, "DEFAULT_VOICE_ID", None)
        if default_voice_id:
            # Lazy import to avoid circular deps at module import time
            from services.voice_service import VoiceService

            try:
                vs = VoiceService(self.settings.VOICES_DIR)
                voice = vs.get_voice(default_voice_id)
                if voice and voice.get("audio_filename"):
                    path = self.settings.VOICES_DIR / voice["audio_filename"]
                    if path.exists():
                        return str(path)
            except Exception:
                # fall back to previous behavior when DB is not available
                pass

        # Previous fallback: first WAV file in VOICES_DIR
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

    async def generate_audio(self, text: str, params: TTSParams | None = None) -> tuple[Any, int]:
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
