"""Core domain interfaces (Ports in Hexagonal Architecture).

This module defines abstract base classes for external dependencies,
ensuring loose coupling between the application/services and infrastructure.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from schemas.internal import TTSParams


class TTSEngineInterface(ABC):
    """Abstract interface for Text-to-Speech engines.

    Allows swapping TTS backends (e.g., Qwen, Coqui, Piper, OpenAI)
    without modifying application-layer logic.
    """

    @abstractmethod
    async def generate_audio(self, text: str, params: TTSParams) -> tuple[Any, int]:
        """Generates an audio waveform from text.

        Returns:
            A tuple of (waveform tensor, sample rate).
        """
        ...

    @abstractmethod
    async def generate_and_save(self, text: str, output_path: str, params: TTSParams) -> str:
        """Generates audio and saves it to a file.

        Returns:
            Path to the saved audio file as a string.
        """
        ...

    @abstractmethod
    def generate_stream(self, text: str, params: TTSParams, chunk_size: int = 4096) -> AsyncGenerator[bytes, None]:
        """Returns an async generator that yields audio byte chunks for streaming."""
        ...


class CacheService(ABC):
    """Abstract interface for caching generated audio assets."""

    @abstractmethod
    def get_key(self, text: str, params: TTSParams) -> str:
        """Generates a unique cache key based on text and parameters."""
        ...

    @abstractmethod
    def get(self, key: str) -> Path | None:
        """Retrieves path to cached audio by its key."""
        ...

    @abstractmethod
    def get_lock(self, key: str) -> asyncio.Lock:
        """Returns an asyncio.Lock associated with a specific cache key."""
        ...

    @abstractmethod
    def set(self, key: str, path: Path) -> None:
        """Stores a path to generated audio in the cache under a specific key."""
        ...


class CleanupService(ABC):
    """Abstract interface for periodic file cleanup tasks."""

    @abstractmethod
    def cleanup_old_files(self, directory: Path, max_age_hours: int = 24) -> int:
        """Removes files in a directory that exceed a maximum age.

        Returns:
            Number of files removed.
        """
        ...


class TTSServiceInterface(ABC):
    """Abstract interface for the main TTS orchestration service."""

    @abstractmethod
    async def generate_from_ssml(self, ssml_content: str, base_params: TTSParams) -> tuple[Path, Path]:
        """Generates audio from SSML content.

        Returns:
            A tuple of (WAV file path, MP3 file path).
        """
        ...

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        language: str,
        mode: str,
        model_size: str,
        reference_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        speaker: str | None = None,
        skip_integrity_check: bool = False,
    ) -> Path:
        """Generates audio from input text and configuration.

        Returns:
            Path to the generated audio file.
        """
        ...

    @abstractmethod
    def generate_stream(
        self,
        text: str,
        language: str,
        mode: str,
        model_size: str,
        reference_audio: str | None = None,
        ref_text: str | None = None,
        instruct: str | None = None,
        speaker: str | None = None,
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """Generates an audio stream from input text and configuration."""
        ...


class VoiceServiceInterface(ABC):
    """Abstract interface for voice management operations."""

    @abstractmethod
    def list_voices(self) -> list[dict]:
        """Lists all registered voices."""
        ...

    @abstractmethod
    def get_voice(self, voice_id: str) -> dict | None:
        """Retrieves voice details by its ID."""
        ...

    @abstractmethod
    def get_voice_by_name(self, name: str) -> dict | None:
        """Retrieves voice details by its name."""
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
        """Creates a new voice entry."""
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
        """Updates an existing voice entry."""
        ...

    @abstractmethod
    def delete_voice(self, voice_id: str) -> bool:
        """Deletes a voice entry."""
        ...

    @abstractmethod
    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Uploads and associates audio reference data with a voice."""
        ...

    @abstractmethod
    def get_audio_path(self, voice_id: str) -> Path | None:
        """Retrieves the file path to a voice's reference audio."""
        ...


class AudioConverter(ABC):
    """Abstract interface for audio file format conversion."""

    @abstractmethod
    def convert_to_mp3(self, input_path: Path) -> Path:
        """Converts an audio file to MP3 format.

        Returns:
            Path to the resulting MP3 file.
        """
        ...
