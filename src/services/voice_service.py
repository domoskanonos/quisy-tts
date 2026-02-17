"""Voice management service – CRUD operations with JSON-based persistence."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from config import ProjectConfig

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


class VoiceService:
    """Service for managing custom voices with JSON file persistence."""

    def __init__(self, voices_dir: Path | None = None) -> None:
        self._voices_dir = voices_dir or settings.VOICES_DIR
        self._registry_path = self._voices_dir / "registry.json"
        self._voices_dir.mkdir(parents=True, exist_ok=True)
        self._registry = self._load_registry()

    # ─── Persistence ─────────────────────────────────────────────

    def _load_registry(self) -> dict[str, dict]:
        """Load voice registry from JSON file."""
        if self._registry_path.exists():
            try:
                data = json.loads(self._registry_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load voice registry: {e}")
        return {}

    def _save_registry(self) -> None:
        """Persist voice registry to JSON file."""
        self._registry_path.write_text(
            json.dumps(self._registry, indent=2, default=str),
            encoding="utf-8",
        )

    # ─── CRUD Operations ─────────────────────────────────────────

    def list_voices(self) -> list[dict]:
        """Return all registered voices, sorted by creation date."""
        voices = list(self._registry.values())
        voices.sort(key=lambda v: v.get("created_at", ""), reverse=True)
        return voices

    def get_voice(self, voice_id: str) -> dict | None:
        """Return a single voice by ID, or None if not found."""
        return self._registry.get(voice_id)

    def create_voice(self, name: str, example_text: str) -> dict:
        """Create a new voice entry (without audio yet)."""
        voice_id = uuid.uuid4().hex[:12]
        now = datetime.now(UTC).isoformat()

        voice = {
            "id": voice_id,
            "name": name,
            "example_text": example_text,
            "audio_filename": None,
            "created_at": now,
            "updated_at": now,
        }

        self._registry[voice_id] = voice
        self._save_registry()
        logger.info(f"Voice created: {voice_id} ({name})")
        return voice

    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
    ) -> dict | None:
        """Update voice metadata. Returns updated voice or None if not found."""
        voice = self._registry.get(voice_id)
        if voice is None:
            return None

        if name is not None:
            voice["name"] = name
        if example_text is not None:
            voice["example_text"] = example_text
        voice["updated_at"] = datetime.now(UTC).isoformat()

        self._save_registry()
        logger.info(f"Voice updated: {voice_id}")
        return voice

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice and its audio file. Returns True if deleted."""
        voice = self._registry.pop(voice_id, None)
        if voice is None:
            return False

        # Remove audio file if exists
        audio_filename = voice.get("audio_filename")
        if audio_filename:
            audio_path = self._voices_dir / audio_filename
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Audio file deleted: {audio_path}")

        self._save_registry()
        logger.info(f"Voice deleted: {voice_id}")
        return True

    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Save or replace the audio file for a voice."""
        voice = self._registry.get(voice_id)
        if voice is None:
            return None

        # Remove old audio file if exists
        old_filename = voice.get("audio_filename")
        if old_filename:
            old_path = self._voices_dir / old_filename
            if old_path.exists():
                old_path.unlink()

        # Determine extension from original filename
        ext = Path(original_filename).suffix or ".wav"
        audio_filename = f"voice_{voice_id}{ext}"
        audio_path = self._voices_dir / audio_filename

        audio_path.write_bytes(audio_data)

        voice["audio_filename"] = audio_filename
        voice["updated_at"] = datetime.now(UTC).isoformat()
        self._save_registry()

        logger.info(f"Audio saved for voice {voice_id}: {audio_filename}")
        return voice

    def get_audio_path(self, voice_id: str) -> Path | None:
        """Return the full path to the audio file for a voice, or None."""
        voice = self._registry.get(voice_id)
        if voice is None or voice.get("audio_filename") is None:
            return None

        audio_path = self._voices_dir / voice["audio_filename"]
        if not audio_path.exists():
            return None

        return audio_path
