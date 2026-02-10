"""Core domain interfaces (Ports in Hexagonal Architecture)."""

from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path
from typing import Any

import torch


class TTSEngine(ABC):
    """Abstract interface for Text-to-Speech engines.

    This interface allows swapping TTS backends (Qwen, Coqui, Piper, OpenAI)
    without changing the application or API layer.
    """

    @abstractmethod
    def generate_audio(self, text: str, params: Any) -> tuple[torch.Tensor, int]:
        """Generate audio waveform from text.

        Args:
            text: The text to convert to speech.
            params: Engine-specific parameters.

        Returns:
            Tuple of (waveform tensor, sample rate).
        """
        ...

    @abstractmethod
    def generate_and_save(self, text: str, output_path: str, params: Any) -> str:
        """Generate audio and save to file.

        Args:
            text: The text to convert to speech.
            output_path: Path to save the audio file.
            params: Engine-specific parameters.

        Returns:
            Path to the saved audio file.
        """
        ...

    @abstractmethod
    def generate_audio_stream(self, text: str, params: Any, chunk_size: int = 4096) -> Generator[bytes, None, None]:
        """Generate audio and yield as byte chunks for streaming.

        Args:
            text: The text to convert to speech.
            params: Engine-specific parameters.
            chunk_size: Size of each chunk in bytes.

        Yields:
            Audio data chunks as bytes.
        """
        ...


class CacheService(ABC):
    """Abstract interface for caching generated audio."""

    @abstractmethod
    def get_key(self, text: str, params: Any) -> str:
        """Generate a cache key from text and parameters.

        Args:
            text: The input text.
            params: Generation parameters.

        Returns:
            A unique cache key string.
        """
        ...

    @abstractmethod
    def get(self, key: str) -> Path | None:
        """Retrieve cached audio by key.

        Args:
            key: The cache key.

        Returns:
            Path to cached file or None if not found.
        """
        ...

    @abstractmethod
    def set(self, key: str, path: Path) -> None:
        """Store audio in cache.

        Args:
            key: The cache key.
            path: Path to the audio file to cache.
        """
        ...


class CleanupService(ABC):
    """Abstract interface for file cleanup operations."""

    @abstractmethod
    def cleanup_old_files(self, directory: Path, max_age_hours: int = 24) -> int:
        """Remove files older than max_age_hours.

        Args:
            directory: Directory to clean.
            max_age_hours: Maximum age of files to keep.

        Returns:
            Number of files removed.
        """
        ...
