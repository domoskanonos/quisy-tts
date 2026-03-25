"""Core domain interfaces (Ports in Hexagonal Architecture)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
import asyncio


class TTSEngine(ABC):
    """Abstract interface for Text-to-Speech engines.

    This interface allows swapping TTS backends (Qwen, Coqui, Piper, OpenAI)
    without changing the application or API layer.
    """

    @abstractmethod
    async def generate_audio(self, text: str, params: Any) -> tuple[Any, int]:
        """Generate audio waveform from text.

        Args:
            text: The text to convert to speech.
            params: Engine-specific parameters.

        Returns:
            Tuple of (waveform tensor, sample rate).
        """
        ...

    @abstractmethod
    async def generate_and_save(self, text: str, output_path: str, params: Any) -> str:
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
    def generate_audio_stream(self, text: str, params: Any, chunk_size: int = 4096) -> AsyncGenerator[bytes, None]:
        """Return an async generator that yields audio byte chunks.

        Implementations should return an async generator (an async def with
        `yield`) which produces bytes for streaming. Keeping this method as a
        synchronous abstractmethod simplifies typing compatibility with
        async generator implementations.
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
    def get_lock(self, key: str) -> "asyncio.Lock":
        """Return an asyncio.Lock for the given cache key.

        This allows callers to perform atomic check+generate+set operations
        guarded by a shared lock owned by the cache implementation.
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
