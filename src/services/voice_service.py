"""Voice management service – Orchestrator for voice operations."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from config import ProjectConfig
from src.core.interfaces import VoiceServiceInterface
from src.repositories.voice_repository import VoiceRepository
from src.services.voice_search_service import VoiceSearchService
from src.services.voice_audio_service import VoiceAudioService

logger = ProjectConfig.get_logger()


class VoiceService(VoiceServiceInterface):
    """Orchestrator for managing voices, delegating to repository and specific services."""

    def __init__(self, voices_dir: Path | None = None, db_path: Path | None = None) -> None:
        settings = ProjectConfig.get_settings()
        self._voices_dir = voices_dir or settings.VOICES_DIR

        # Determine DB path
        db_destination = settings.APP_DIR / "quisy-tts.db"
        self._db_path = Path(db_path) if db_path is not None else db_destination

        # Initialize components
        self.repository = VoiceRepository(self._db_path)
        self.audio_service = VoiceAudioService(self._voices_dir)
        self.search_service = VoiceSearchService(self._db_path)

    # ─── Orchestration methods ──────────────────────────────────

    def list_voices(self) -> list[dict]:
        return self.repository.list_all()

    def get_voice(self, voice_id: str) -> dict | None:
        return self.repository.get_by_id(voice_id)

    def get_voice_by_name(self, name: str) -> dict | None:
        return self.repository.get_by_name(name)

    def search(self, terms: list[str], q: str | None, limit: int = 20, offset: int = 0) -> list[dict]:
        return self.search_service.search(terms, q, limit, offset)

    def get_top_instruct_terms(self) -> list[dict]:
        return self.search_service.get_top_instruct_terms()

    def create_voice(
        self,
        name: str,
        example_text: str,
        voice_id: str | None = None,
        instruct: str | None = None,
        language: str = "german",
    ) -> dict | None:
        """Create a new user voice."""
        if not example_text or not example_text.strip():
            raise ValueError("example_text is mandatory for creating a new voice.")

        import uuid

        # Generate a new unique voice_id if not provided
        if voice_id is None:
            voice_id = uuid.uuid4().hex[:12]

        if self.repository.get_by_id(voice_id) is not None:
            raise ValueError(f"Voice with ID {voice_id} already exists.")

        return self.repository.create(voice_id, name, example_text, instruct, language)

    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
        instruct: str | None = None,
        description: str | None = None,
        language: str | None = None,
    ) -> dict | None:
        """Update voice metadata."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return None

        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if example_text is not None:
            updates["example_text"] = example_text
        if instruct is not None:
            updates["instruct"] = instruct
        if description is not None:
            updates["description"] = description
        if language is not None:
            updates["language"] = language

        if not updates:
            return voice

        return self.repository.update(voice_id, updates)

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice and its audio file."""
        if self.repository.get_by_id(voice_id) is None:
            return False

        self.audio_service.delete_audio(voice_id)
        return self.repository.delete(voice_id)

    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Save or replace the audio file for a voice."""
        if self.repository.get_by_id(voice_id) is None:
            return None

        self.audio_service.save_audio(voice_id, audio_data)
        # Update timestamp
        return self.repository.update(voice_id, {"updated_at": datetime.now(UTC).isoformat()})

    def get_audio_path(self, voice_id: str) -> Path | None:
        voice = self.get_voice(voice_id)
        if not voice:
            return None
        return self.audio_service.get_audio_path(voice_id, voice.get("audio_filename"))

    def get_voice_filename(self, voice_id: str) -> str:
        """Centralized naming convention for voice files."""
        return self.audio_service.get_filename(voice_id)
