from collections.abc import Generator
from typing import Protocol

import torch

from schemas import TTSParams


class TTSBackend(Protocol):
    """Protocol for TTS backends (Transformers vs vLLM)."""

    def generate_audio(self, text: str, params: TTSParams) -> tuple[torch.Tensor, int]:
        """Generate audio waveform."""
        ...

    def generate_audio_stream(
        self, text: str, params: TTSParams, chunk_size: int = 4096
    ) -> Generator[bytes, None, None]:
        """Generate audio stream."""
        ...
