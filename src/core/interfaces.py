"""Core domain interfaces (Ports in Hexagonal Architecture).

This module defines abstract base classes for external dependencies,
ensuring loose coupling between the application/services and infrastructure.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
import asyncio


class TTSEngineInterface(ABC):
    """Abstract interface for Text-to-Speech engines.

    Allows swapping TTS backends (e.g., Qwen, Coqui, Piper, OpenAI)
    without modifying application-layer logic.
    """

    @abstractmethod
    async def generate_audio(self, text: str, params: Any) -> tuple[Any, int]:
        """Generates an audio waveform from text.

        Args:
            text: The text to be converted to speech.
            params: Engine-specific generation parameters.

        Returns:
            A tuple of (waveform tensor, sample rate).
        """
        ...

    @abstractmethod
    async def generate_and_save(self, text: str, output_path: str, params: Any) -> str:
        """Generates audio and saves it to a file.

        Args:
            text: The text to be converted to speech.
            output_path: Path to the destination audio file.
            params: Engine-specific generation parameters.

        Returns:
            Path to the saved audio file as a string.
        """
        ...

    @abstractmethod
    def generate_stream(self, text: str, params: Any, chunk_size: int = 4096) -> AsyncGenerator[bytes, None]:
        """Returns an async generator that yields audio byte chunks for streaming.

        Args:
            text: The text to be converted to speech.
            params: Engine-specific generation parameters.
            chunk_size: Size of byte chunks to yield.

        Yields:
            Audio bytes chunks.
        """
        ...


class CacheService(ABC):
    """Abstract interface for caching generated audio assets."""

    @abstractmethod
    def get_key(self, text: str, params: Any) -> str:
        """Generates a unique cache key based on text and parameters.

        Args:
            text: The input text.
            params: Generation parameters.

        Returns:
            A unique cache key string.
        """
        ...

    @abstractmethod
    def get(self, key: str) -> Path | None:
        """Retrieves path to cached audio by its key.

        Args:
            key: The cache key.

        Returns:
            Path to the cached audio file, or None if not found.
        """
        ...

    @abstractmethod
    def get_lock(self, key: str) -> "asyncio.Lock":
        """Returns an asyncio.Lock associated with a specific cache key.

        This facilitates atomic check-generate-set operations by preventing
        concurrent generation of the same asset.
        """
        ...

    @abstractmethod
    def set(self, key: str, path: Path) -> None:
        """Stores a path to generated audio in the cache under a specific key.

        Args:
            key: The cache key.
            path: Path to the generated audio file.
        """
        ...


class CleanupService(ABC):
    """Abstract interface for periodic file cleanup tasks."""

    @abstractmethod
    def cleanup_old_files(self, directory: Path, max_age_hours: int = 24) -> int:
        """Removes files in a directory that exceed a maximum age.

        Args:
            directory: Directory to clean.
            max_age_hours: Age threshold in hours.

        Returns:
            Number of files removed.
        """
        ...


class TTSServiceInterface(ABC):
    """Abstract interface for the main TTS orchestration service."""

    @abstractmethod
    async def generate_from_ssml(self, ssml_content: str, base_params: Any) -> tuple[Path, Path]:
        """Generates audio from SSML content.

        Args:
            ssml_content: The SSML markup string.
            base_params: Global generation parameters.

        Returns:
            A tuple of (WAV file path, MP3 file path).
        """
        ...

    @abstractmethod
    async def generate_audio(self, *args: Any, **kwargs: Any) -> Path:
        """Generates audio from input text and configuration.

        Returns:
            Path to the generated audio file.
        """
        ...

    @abstractmethod
    def generate_stream(self, *args: Any, **kwargs: Any) -> AsyncGenerator[bytes, None]:
        """Generates an audio stream from input text and configuration.

        Yields:
            Audio bytes chunks.
        """
        ...


class VoiceServiceInterface(ABC):
    """Abstract interface for voice management operations."""

    @abstractmethod
    def list_voices(self) -> list[dict]:
        """Lists all registered voices.

        Returns:
            A list of voice configuration dictionaries.
        """
        ...

    @abstractmethod
    def get_voice(self, voice_id: str) -> dict | None:
        """Retrieves voice details by its ID.

        Args:
            voice_id: The unique identifier of the voice.

        Returns:
            The voice configuration dictionary, or None if not found.
        """
        ...

    @abstractmethod
    def get_voice_by_name(self, name: str) -> dict | None:
        """Retrieves voice details by its name.

        Args:
            name: The display name of the voice.

        Returns:
            The voice configuration dictionary, or None if not found.
        """
        ...

    @abstractmethod
    def create_voice(
        self,
        name: str,
        example_text: str,
        voice_id: str | None = None,
        instruct: str | None = None,
        description: str | None = None,
        language: str = "german",
    ) -> dict | None:
        """Creates a new voice entry.

        Returns:
            The created voice configuration, or None if creation fails.
        """
        ...

    @abstractmethod
    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
        instruct: str | None = None,
        description: str | None = None,
        language: str | None = None,
    ) -> dict | None:
        """Updates an existing voice entry.

        Returns:
            The updated voice configuration, or None if update fails.
        """
        ...

    @abstractmethod
    def delete_voice(self, voice_id: str) -> bool:
        """Deletes a voice entry.

        Args:
            voice_id: The unique identifier of the voice to delete.

        Returns:
            True if successfully deleted, False otherwise.
        """
        ...

    @abstractmethod
    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Uploads and associates audio reference data with a voice.

        Returns:
            The updated voice configuration, or None if update fails.
        """
        ...

    @abstractmethod
    def get_audio_path(self, voice_id: str) -> Path | None:
        """Retrieves the file path to a voice's reference audio.

        Args:
            voice_id: The unique identifier of the voice.

        Returns:
            Path to the audio file, or None if not available.
        """
        ...


class AudioConverter(ABC):
    """Abstract interface for audio file format conversion."""

    @abstractmethod
    def convert_to_mp3(self, input_path: Path) -> Path:
        """Converts an audio file to MP3 format.

        Args:
            input_path: Path to the input audio file (typically WAV).

        Returns:
            Path to the resulting MP3 file.
        """
        ...
