"""Voice management service – CRUD operations with SQLite persistence."""

import shutil
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from config import ProjectConfig
from services.default_voices import DEFAULT_VOICES

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS voices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    example_text TEXT NOT NULL,
    instruct TEXT,
    language TEXT NOT NULL DEFAULT 'german',
    audio_filename TEXT,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class VoiceService:
    """Service for managing voices with SQLite persistence."""

    def __init__(self, voices_dir: Path | None = None) -> None:
        self._voices_dir = voices_dir or settings.VOICES_DIR
        self._voices_dir.mkdir(parents=True, exist_ok=True)

        # Database now lives in APP_DIR
        self._app_dir = settings.APP_DIR
        self._app_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._app_dir / "quisy-tts.db"

        # Check if DB exists. If not, try to copy from resources
        if not self._db_path.exists():
            resource_db_path = settings.RESOURCES_DIR / "quisy-tts.db"
            if resource_db_path.exists():
                logger.info(f"Checking for database seeding: Copying {resource_db_path} to {self._db_path}")
                shutil.copy2(resource_db_path, self._db_path)
            else:
                logger.info("No seed database found in resources. Starting fresh.")

        self._init_db()

    # ─── Database Setup ──────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Create a new connection with row_factory."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create table, run migrations, and seed default voices if empty."""
        with self._get_conn() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            self._migrate(conn)

            # Check if default voices already exist
            count = conn.execute("SELECT COUNT(*) FROM voices WHERE is_default = 1").fetchone()[0]

            if count == 0:
                self._seed_defaults(conn)
                logger.info(f"Seeded {len(DEFAULT_VOICES)} default voices into SQLite.")

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Run schema migrations for existing databases."""
        # Check if 'language' column exists
        columns = {row[1] for row in conn.execute("PRAGMA table_info(voices)").fetchall()}
        if "language" not in columns:
            logger.info("Migrating voices table: adding 'language' column...")
            conn.execute("ALTER TABLE voices ADD COLUMN language TEXT NOT NULL DEFAULT 'german'")
            conn.commit()

    def _seed_defaults(self, conn: sqlite3.Connection) -> None:
        """Insert all default voices."""
        now = datetime.now(UTC).isoformat()
        for i, voice in enumerate(DEFAULT_VOICES):
            voice_id = f"default_{i + 1:03d}"
            conn.execute(
                """INSERT INTO voices (id, name, example_text, instruct, language, audio_filename, is_default, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, NULL, 1, ?, ?)""",
                (
                    voice_id,
                    voice["name"],
                    voice["example_text"],
                    voice["instruct"],
                    voice.get("language", "german"),
                    now,
                    now,
                ),
            )

    # ─── Helper ──────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a sqlite3.Row to a plain dict."""
        return {
            "id": row["id"],
            "name": row["name"],
            "example_text": row["example_text"],
            "instruct": row["instruct"],
            "language": row["language"],
            "audio_filename": row["audio_filename"],
            "is_default": bool(row["is_default"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # ─── CRUD Operations ─────────────────────────────────────────

    def list_voices(self) -> list[dict]:
        """Return all voices, defaults first then by creation date."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM voices ORDER BY is_default DESC, name ASC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_voice(self, voice_id: str) -> dict | None:
        """Return a single voice by ID, or None if not found."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE id = ?", (voice_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_voice_by_name(self, name: str) -> dict | None:
        """Return a single voice by name, or None if not found."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE name = ?", (name,)).fetchone()
        return self._row_to_dict(row) if row else None

    def create_voice(
        self,
        name: str,
        example_text: str,
        instruct: str | None = None,
        language: str = "german",
    ) -> dict:
        """Create a new user voice."""
        voice_id = uuid.uuid4().hex[:12]
        now = datetime.now(UTC).isoformat()

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO voices (id, name, example_text, instruct, language, audio_filename, is_default, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, NULL, 0, ?, ?)""",
                (voice_id, name, example_text, instruct, language, now, now),
            )

        logger.info(f"Voice created: {voice_id} ({name})")
        return self.get_voice(voice_id)  # type: ignore[return-value]

    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
        instruct: str | None = None,
        language: str | None = None,
    ) -> dict | None:
        """Update voice metadata. Returns updated voice or None if not found."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return None

        now = datetime.now(UTC).isoformat()
        updates: list[str] = []
        params: list[str | None] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if example_text is not None:
            updates.append("example_text = ?")
            params.append(example_text)
        if instruct is not None:
            updates.append("instruct = ?")
            params.append(instruct)
        if language is not None:
            updates.append("language = ?")
            params.append(language)

        if not updates:
            return voice

        updates.append("updated_at = ?")
        params.append(now)
        params.append(voice_id)

        sql = f"UPDATE voices SET {', '.join(updates)} WHERE id = ?"  # noqa: S608

        with self._get_conn() as conn:
            conn.execute(sql, params)

        logger.info(f"Voice updated: {voice_id}")
        return self.get_voice(voice_id)

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice and its audio file. Returns True if deleted."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return False

        if voice.get("is_default"):
            return False  # Default voices cannot be deleted

        # Remove audio file if exists
        audio_filename = voice.get("audio_filename")
        if audio_filename:
            audio_path = self._voices_dir / audio_filename
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Audio file deleted: {audio_path}")

        with self._get_conn() as conn:
            conn.execute("DELETE FROM voices WHERE id = ?", (voice_id,))

        logger.info(f"Voice deleted: {voice_id}")
        return True

    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Save or replace the audio file for a voice."""
        voice = self.get_voice(voice_id)
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

        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE voices SET audio_filename = ?, updated_at = ? WHERE id = ?",
                (audio_filename, now, voice_id),
            )

        logger.info(f"Audio saved for voice {voice_id}: {audio_filename}")
        return self.get_voice(voice_id)

    def get_audio_path(self, voice_id: str) -> Path | None:
        """Return the full path to the audio file for a voice, or None."""
        voice = self.get_voice(voice_id)
        if voice is None or voice.get("audio_filename") is None:
            return None

        audio_path = self._voices_dir / voice["audio_filename"]
        if not audio_path.exists():
            return None

        return audio_path
