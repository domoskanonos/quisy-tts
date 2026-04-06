"""Voice management service – CRUD operations with SQLite persistence."""

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from config import ProjectConfig
from src.core.interfaces import VoiceServiceInterface
from src.schemas.languages import resolve_language
from domain.voice.models import Voice


logger = ProjectConfig.get_logger()


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS voices (
    voice_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    example_text TEXT NOT NULL,
    instruct TEXT,
    voice_name TEXT,
    language TEXT NOT NULL DEFAULT 'german',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class VoiceService(VoiceServiceInterface):
    """Service for managing voices with SQLite persistence."""

    def __init__(self, voices_dir: Path | None = None, db_path: Path | None = None) -> None:
        settings = ProjectConfig.get_settings()
        self._voices_dir = voices_dir or settings.VOICES_DIR
        logger.debug(f"VoiceService init. voices_dir={self._voices_dir}, CWD={Path.cwd()}")
        self._voices_dir.mkdir(parents=True, exist_ok=True)

        # Use either provided db_path (useful for tests) or a copy of the resources DB
        # in data/app_data as the single authoritative, writable runtime DB.
        db_destination = settings.APP_DIR / "quisy-tts.db"
        if db_path is not None:
            self._db_path = Path(db_path)
        else:
            self._db_path = db_destination
            # Ensure the directory exists
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            # Copy if not exists
            if not self._db_path.exists():
                import shutil

                source_db = settings.RESOURCES_DIR / "quisy-tts.db"
                if source_db.exists():
                    shutil.copy2(source_db, self._db_path)
                    logger.info(f"Copied resources DB to {self._db_path}")
                else:
                    # Fallback to create empty if source not found
                    import sqlite3 as _sqlite

                    conn = _sqlite.connect(str(self._db_path))
                    conn.commit()
                    conn.close()
                    logger.info(f"Created new DB at {self._db_path}")

        # Ensure we can write to the runtime DB
        try:
            with open(self._db_path, "ab"):
                pass
        except Exception as e:
            logger.error(f"resources DB at {self._db_path} is not writable: {e}")
            raise

        # Initialize DB (run migrations / seed) directly on resources DB
        self._init_db()

    # ─── Database Setup ──────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Create a new connection with row_factory."""
        # Enable WAL for better concurrency and performance
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            # Not critical if PRAGMA is unsupported
            pass
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create table and run migrations."""
        with self._get_conn() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Run schema migrations for existing databases."""
        # Check if 'voice_name' column exists (and rename 'description' if it exists from previous step)
        cursor = conn.execute("PRAGMA table_info(voices)")
        columns = {row[1]: row for row in cursor.fetchall()}

        if "voice_name" not in columns:
            if "description" in columns:
                logger.info("Migrating database: Renaming 'description' column to 'voice_name' in 'voices' table.")
                conn.execute("ALTER TABLE voices RENAME COLUMN description TO voice_name")
            else:
                logger.info("Migrating database: Adding 'voice_name' column to 'voices' table.")
                conn.execute("ALTER TABLE voices ADD COLUMN voice_name TEXT")
            conn.commit()

    # ─── Helper ──────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        """Convert a sqlite3.Row to a plain dict."""
        data = {
            "voice_id": row["voice_id"],
            "name": row["name"],
            "example_text": row["example_text"],
            "instruct": row["instruct"],
            "language": row["language"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        # Safely handle 'voice_name' if it exists (for migration support)
        if "voice_name" in row.keys():
            data["voice_name"] = row["voice_name"]
        else:
            data["voice_name"] = None
        return data

    @staticmethod
    def get_voice_filename(voice_id: str) -> str:
        """Centralized naming convention for voice files."""
        return Voice.get_filename(voice_id)

    def list_voices(self) -> list[dict]:
        """Return all voices, defaults first then by creation date."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM voices ORDER BY name ASC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ─── FTS / Search Helpers ─────────────────────────────────────

    def get_top_instruct_terms(self) -> list[dict]:
        """Return top terms from the FTS index via simple token counts.

        If FTS isn't available, fall back to an empty list.
        """
        with self._get_conn() as conn:
            try:
                # Use FTS auxiliary function to enumerate tokens if available.
                # SQLite doesn't expose token counts directly, so we'll approximate
                # by splitting instructs and counting tokens here.
                rows = conn.execute("SELECT instruct FROM voices WHERE instruct IS NOT NULL").fetchall()
                from collections import Counter
                import re

                counter: Counter[str] = Counter()
                for r in rows:
                    text = r[0] or ""
                    tokens = re.findall(r"\b\w{3,}\b", text.lower(), flags=re.UNICODE)
                    counter.update(tokens)

                top = counter.most_common(50)
                return [{"term": t, "count": c} for t, c in top]
            except Exception:
                return []

    def search(self, terms: list[str], q: str | None, limit: int = 20, offset: int = 0) -> list[dict]:
        """Search voices using FTS5 MATCH where possible, falling back to LIKE.

        - `terms` are treated as ANDed tokens that must appear in `instruct`.
        - `q` is a free text query applied across `name`, `instruct`, `example_text`.
        """
        with self._get_conn() as conn:
            try:
                # Prefer FTS5 if available
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voices_fts'")
                if cur.fetchone():
                    clauses = []
                    params: list[str] = []
                    if terms:
                        # Build MATCH expression requiring all terms (AND semantics)
                        match_expr = " AND ".join([t for t in terms])
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(match_expr)
                    if q:
                        # Use FTS MATCH for free text as well (allow prefix searching)
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(q + "*")

                    where = " AND ".join(clauses) if clauses else "1=1"
                    sql = f"SELECT * FROM voices WHERE {where} ORDER BY name ASC LIMIT ? OFFSET ?"
                    params.extend([str(limit), str(offset)])
                    rows = conn.execute(sql, params).fetchall()
                    return [self._row_to_dict(r) for r in rows]
            except Exception:
                # Fall through to LIKE-based fallback
                pass

            # Fallback: simple LIKE-based search
            parts: list[str] = []
            like_params: list[str] = []
            for t in terms:
                parts.append("instruct LIKE ?")
                like_params.append(f"%{t}%")
            if q:
                parts.append("(name LIKE ? OR instruct LIKE ? OR example_text LIKE ?)")
                like_params.extend([f"%{q}%"] * 3)

            where = " AND ".join(parts) if parts else "1=1"
            sql = f"SELECT * FROM voices WHERE {where} ORDER BY name ASC LIMIT ? OFFSET ?"
            like_params.extend([str(limit), str(offset)])
            rows = conn.execute(sql, like_params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_voice(self, voice_id: str) -> dict | None:
        """Return a single voice by ID, or None if not found."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE voice_id = ?", (voice_id,)).fetchone()
        return self._row_to_dict(row) if row is not None else None

    def get_voice_by_name(self, name: str) -> dict | None:
        """Return a single voice by name, or None if not found."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE name = ?", (name,)).fetchone()
        return self._row_to_dict(row) if row is not None else None

    def create_voice(
        self,
        name: str,
        example_text: str,
        instruct: str | None = None,
        voice_name: str | None = None,
        language: str = "german",
    ) -> dict | None:
        """Create a new user voice."""
        if not example_text or not example_text.strip():
            raise ValueError("example_text is mandatory for creating a new voice.")

        # If the caller provided a friendly identifier (alphanumeric, underscore,
        # or dash) try to use it as the voice ID so external tools can reference
        # it predictably. If that ID already exists, append a numeric suffix to
        # make it unique. Otherwise fall back to a short uuid.
        import re

        def _id_available(cid: str) -> bool:
            with self._get_conn() as conn:
                row = conn.execute("SELECT 1 FROM voices WHERE voice_id = ? LIMIT 1", (cid,)).fetchone()
                return row is None

        if name and re.match(r"^[a-zA-Z0-9_-]{1,100}$", name) and _id_available(name):
            voice_id = name
        elif name and re.match(r"^[a-zA-Z0-9_-]{1,100}$", name):
            # Try suffixes to find an available id
            for i in range(1, 1001):
                candidate = f"{name}-{i}"
                if _id_available(candidate):
                    voice_id = candidate
                    break
            else:
                voice_id = uuid.uuid4().hex[:12]
        else:
            voice_id = uuid.uuid4().hex[:12]
        now = datetime.now(UTC).isoformat()

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO voices (voice_id, name, example_text, instruct, voice_name, language, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (voice_id, name, example_text, instruct, voice_name, resolve_language(language), now, now),
            )
            # Rebuild FTS index if it exists
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError:
                pass
            conn.commit()

        return self.get_voice(voice_id)

    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
        instruct: str | None = None,
        voice_name: str | None = None,
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
        if voice_name is not None:
            updates.append("voice_name = ?")
            params.append(voice_name)
        if language is not None:
            updates.append("language = ?")
            params.append(language)

        # system_prompt removed from update fields

        if not updates:
            return voice

        updates.append("updated_at = ?")
        params.append(now)
        params.append(voice_id)

        sql = f"UPDATE voices SET {', '.join(updates)} WHERE voice_id = ?"  # noqa: S608

        with self._get_conn() as conn:
            conn.execute(sql, params)

        logger.info(f"Voice updated: {voice_id}")
        return self.get_voice(voice_id)

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice and its audio file. Returns True if deleted."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return False

        # Remove audio file if exists
        audio_path = self._voices_dir / self.get_voice_filename(voice_id)
        if audio_path.exists():
            audio_path.unlink()
            logger.info(f"Audio file deleted: {audio_path}")

        with self._get_conn() as conn:
            conn.execute("DELETE FROM voices WHERE voice_id = ?", (voice_id,))
            # Rebuild FTS index if it exists
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError:
                pass
            conn.commit()

        logger.info(f"Voice deleted: {voice_id}")
        return True

    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        """Save or replace the audio file for a voice."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return None

        # Always use voice_{voice_id}.wav
        final_filename = self.get_voice_filename(voice_id)
        audio_path = self._voices_dir / final_filename
        audio_path.write_bytes(audio_data)

        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE voices SET updated_at = ? WHERE voice_id = ?",
                (now, voice_id),
            )
            conn.commit()

        logger.info(f"Audio saved for voice {voice_id}: {final_filename}")
        return self.get_voice(voice_id)

    def get_audio_path(self, voice_id: str) -> Path | None:
        """Return the full path to the audio file for a voice, or None."""
        voice = self.get_voice(voice_id)
        if voice is None or voice.get("audio_filename") is None:
            return None

        # Only serve generated audio from the voices directory. Resources/voices
        # shipped with the project are explicitly ignored per runtime policy.
        filename = voice["audio_filename"]
        if not filename:
            return None

        audio_path = self._voices_dir / filename
        if not audio_path.exists():
            return None
        return audio_path
