"""Qwen3-TTS engine implementation using the official qwen-tts package."""

import asyncio
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import numpy as np
from qwen_tts import Qwen3TTSModel

from audio.processor import AudioUtils
from config import ProjectConfig
from core import TTSEngine
from schemas import TTSParams
from schemas.languages import resolve_language
from services.text_splitter import get_text_splitter

logger = ProjectConfig.get_logger()

# Centralized generation config for consistency
QWEN_GENERATION_CONFIG = {
    "temperature": 0.8,
    "top_p": 1.0,
    "top_k": 50,
    "repetition_penalty": 1.05,
    "max_new_tokens": 2048,
}

# Silence duration between chunks in seconds
INTER_CHUNK_SILENCE_SECS = 0.15


class QwenTextToSpeech(TTSEngine):
    """Qwen3-TTS implementation using the official qwen-tts package (Async).
    Loads separate models per generation mode lazily on first use.
    """

    def __init__(self) -> None:
        """Initialize the Qwen Text-to-Speech engine."""
        self.settings = ProjectConfig.get_settings()
        logger.info("Initializing Qwen3-TTS backend (Lazy, multi-model)...")

        self._models: dict[str, Qwen3TTSModel] = {}

        # Determine model map based on configured version
        version = self.settings.MODEL
        if version == "1.7":
            self.model_map = {
                "base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "custom": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            }
        elif version == "0.6":
            self.model_map = {
                "base": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
                "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "custom": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            }
        else:
            raise ValueError(f"Unsupported model version: {version}")

        self._locks: dict[str, asyncio.Lock] = {mode: asyncio.Lock() for mode in self.model_map}
        self._text_splitter = get_text_splitter()

    async def ensure_loaded(self, mode: str = "base") -> Qwen3TTSModel:
        """Ensure the model for a given mode is loaded. Safe to call concurrently."""
        if mode in self._models:
            return self._models[mode]

        lock = self._locks.get(mode)
        if lock is None:
            raise ValueError(f"Unknown mode: {mode}. Available: {list(self.model_map.keys())}")

        async with lock:
            if mode in self._models:
                return self._models[mode]

            model_name = self.model_map[mode]
            logger.info(f"Loading Qwen3-TTS model for mode '{mode}': {model_name}...")
            start_time = time.time()

            # Run blocking model load in thread pool
            loop = asyncio.get_running_loop()
            try:
                model = await loop.run_in_executor(None, self._load_model_sync, model_name)
            except OSError as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise ValueError(f"Could not load model {model_name}. Please verify the model identifier.") from e

            self._models[mode] = model

            elapsed = time.time() - start_time
            logger.info(f"Qwen3-TTS model '{mode}' loaded successfully in {elapsed:.2f}s")
            return model

    def _load_model_sync(self, model_name: str) -> Qwen3TTSModel:
        """Synchronous model loading (runs in thread)."""
        import torch

        kwargs: dict[str, Any] = {"device_map": "auto", "attn_implementation": "sdpa"}
        dtype = getattr(torch, "bfloat16", None)
        if dtype is not None:
            kwargs["dtype"] = dtype
        return Qwen3TTSModel.from_pretrained(model_name, **kwargs)

    async def generate_audio(self, text: str, params: Any = None) -> tuple[Any, int]:
        """Generates audio waveform via qwen-tts (async)."""
        if params is None:
            params = TTSParams()

        logger.info(f"Starting audio generation | Mode: {params.mode} | Text Length: {len(text)}")
        model = await self.ensure_loaded(params.mode)
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

        if not params.language:
            raise ValueError("language must be provided in TTSParams for generation")

        resolved_lang = getattr(params, "resolved_language", None) or resolve_language(params.language)

        loop = asyncio.get_running_loop()
        wavs, sr = await loop.run_in_executor(
            None,
            lambda: self._generate_sync(model, text, params, resolved_lang, gen_kwargs),
        )

        import torch

        audio_tensor = torch.from_numpy(wavs[0]).float().unsqueeze(0)
        return audio_tensor, sr

    def _generate_sync(
        self, model: Qwen3TTSModel, text: str, params: TTSParams, resolved_lang: str, gen_kwargs: dict
    ) -> tuple[list, int]:
        """Synchronous generation logic."""
        if params.mode == "voice_design":
            return model.generate_voice_design(
                text=text, language=resolved_lang, instruct=params.instruct or "", **gen_kwargs
            )

        # Base/Custom mode = voice clone
        ref_audio_path = self._resolve_ref_audio(params)
        logger.debug(
            f"Debug: _generate_sync | ref_audio_path: {ref_audio_path} | ref_text length: {len(params.ref_text or '')} | ref_text: '{params.ref_text}'"
        )
        if not ref_audio_path:
            from core.exceptions import ReferenceAudioNotFoundError

            raise ReferenceAudioNotFoundError("No reference audio found.")

        return model.generate_voice_clone(
            text=text, language=resolved_lang, ref_audio=ref_audio_path, ref_text=params.ref_text or "", **gen_kwargs
        )

    async def generate_and_save(self, text: str, output_path: str, params: Any = None) -> str:
        """Generates audio and saves it to a file (async)."""
        if params is None:
            params = TTSParams()
        waveform, sr = await self.generate_audio(text, params)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, AudioUtils.save_waveform, waveform, sr, output_path)
        return output_path

    def generate_audio_stream(
        self, text: str, params: Any = None, chunk_size: int = 4096
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio by generating a single text chunk and yielding bytes."""
        if params is None:
            params = TTSParams()

        async def _generator():
            waveform, _ = await self.generate_audio(text, params)
            audio_np = waveform.squeeze().cpu().numpy()
            audio_bytes = (audio_np * 32767).astype(np.int16).tobytes()
            for k in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[k : k + chunk_size]

        return _generator()

    def _resolve_ref_audio(self, params: TTSParams) -> str | None:
        """Resolve reference audio path."""
        from services.voice_service import VoiceService

        if params.reference_audio:
            path = self.settings.VOICES_DIR / VoiceService.get_voice_filename(params.reference_audio)
            if path.exists():
                return str(path)

        default_voice_id = getattr(self.settings, "DEFAULT_VOICE_ID", None)
        if default_voice_id:
            vs = VoiceService(self.settings.VOICES_DIR)
            voice = vs.get_voice(default_voice_id)
            if voice:
                path = self.settings.VOICES_DIR / VoiceService.get_voice_filename(default_voice_id)
                if path.exists():
                    return str(path)

        voices = list(self.settings.VOICES_DIR.glob("*.wav"))
        return str(voices[0]) if voices else None
