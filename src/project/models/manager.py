from typing import Any

import torch
from qwen_tts import Qwen3TTSModel

from project.config import ProjectConfig


logger = ProjectConfig.get_logger()


class ModelManager:
    """Manages loading and caching of Qwen3-TTS models."""

    _models: dict[str, Any] = {}
    MIN_BF16_CAPABILITY = 8

    @classmethod
    def get_model_id(cls, mode: str, size: str) -> str:
        """Determines the Hugging Face model ID based on mode and size."""
        suffix = mode.capitalize() if mode != "base" else "Base"
        # Map capitalized name to exact model name parts
        if suffix == "Voice_design":
            suffix = "VoiceDesign"
        if suffix == "Custom_voice":
            suffix = "CustomVoice"

        return f"Qwen/Qwen3-TTS-12Hz-{size}-{suffix}"

    @classmethod
    def get_model(cls, mode: str = "base", size: str | None = None) -> Qwen3TTSModel:
        """Retrieves or loads the requested model."""
        settings = ProjectConfig.get_settings()
        if not size:
            raise ValueError("Model size must be specified (e.g. '0.6B' or '1.7B')")

        # Safety check for 0.6B VoiceDesign (not available)
        if size == "0.6B" and mode == "voice_design":
            logger.warning(
                "0.6B model does not support VoiceDesign. Falling back to 1.7B."
            )
            size = "1.7B"

        model_id = cls.get_model_id(mode, size)

        if model_id in cls._models:
            logger.info(f"Model {model_id} found in cache. Using cached instance.")
            return cls._models[model_id]

        logger.info(f"Initializing model loading pipeline for: {model_id}")

        device = settings.DEVICE
        if device == "cuda" and not torch.cuda.is_available():
            logger.critical(
                "CUDA usage requested but not available. "
                "Please verify your GPU configuration or set "
                "DEVICE='cpu' in your settings."
            )
            raise RuntimeError("CUDA unavailable but requested.")

        if device == "cuda":
            dtype = (
                torch.bfloat16
                if torch.cuda.get_device_capability(0)[0] >= cls.MIN_BF16_CAPABILITY
                else torch.float16
            )
        else:
            dtype = torch.float32

        logger.info(f"Hardware Configuration | Device: {device} | Dtype: {dtype}")

        # Local-first loading
        local_path = settings.MODELS_DIR / model_id.replace("/", "--")
        load_path = str(local_path) if local_path.exists() else model_id

        if local_path.exists():
            logger.info(f"Using local model checkpoint at {local_path}")
        else:
            logger.info(
                f"Model not found locally, downloading from Hugging Face: {model_id}"
            )

        # Try to use Flash Attention 2 for faster inference
        try:
            model = Qwen3TTSModel.from_pretrained(
                load_path,
                device_map=device,
                torch_dtype=dtype,
                attn_implementation="flash_attention_2",
            )
            logger.info(f"Successfully loaded {model_id} with Flash Attention 2")
        except Exception as e:
            logger.warning(
                f"Flash Attention 2 not available: {e}. Using default attention."
            )
            model = Qwen3TTSModel.from_pretrained(
                load_path,
                device_map=device,
                torch_dtype=dtype,
            )
            logger.info(f"Successfully loaded {model_id} with default attention")

        cls._models[model_id] = model

        # Ensure directories exist
        settings.VOICES_DIR.mkdir(parents=True, exist_ok=True)
        settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        return model
