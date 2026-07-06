import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import ProjectConfig
from schemas.languages import resolve_language

logger = logging.getLogger("project")


class VoiceRepository:
    """Repository for CRUD operations on voice metadata."""

    _ALLOWED_UPDATE_COLUMNS = frozenset({"name", "example_text", "instruct", "description", "language", "updated_at"})

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        import shutil

        if not self._db_path.parent.exists():
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._db_path.exists():
            resource_db = ProjectConfig.get_settings().RESOURCES_DIR / "quisy-tts.db"
            logger.debug(f"Checking for database at {resource_db}, exists: {resource_db.exists()}")
            if resource_db.exists():
                shutil.copy2(resource_db, self._db_path)
            else:
                raise FileNotFoundError(f"Resources database not found at {resource_db}")

        with self._get_conn() as conn:
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        cursor = conn.execute("PRAGMA table_info(voices)")
        columns = {row[1]: row for row in cursor.fetchall()}

        if "voice_name" in columns:
            conn.execute(
                "CREATE TABLE voices_new AS SELECT voice_id, name, example_text, instruct, language, created_at, updated_at FROM voices"
            )
            conn.execute("DROP TABLE voices")
            conn.execute("ALTER TABLE voices_new RENAME TO voices")
            conn.execute("CREATE UNIQUE INDEX idx_voices_voice_id ON voices(voice_id)")
            conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        return {
            "voice_id": row["voice_id"],
            "name": row["name"],
            "example_text": row["example_text"],
            "instruct": row["instruct"],
            "language": row["language"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_all(self) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM voices ORDER BY name ASC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_by_id(self, voice_id: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE voice_id = ?", (voice_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_by_name(self, name: str) -> dict | None:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE name = ?", (name,)).fetchone()
        return self._row_to_dict(row) if row else None

    def create(self, voice_id: str, name: str, example_text: str, instruct: str | None, language: str) -> dict | None:
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO voices (voice_id, name, example_text, instruct, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (voice_id, name, example_text, instruct, resolve_language(language), now, now),
            )
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError as e:
                logger.debug(f"FTS rebuild skipped (table may not exist): {e}")
            conn.commit()
        return self.get_by_id(voice_id)

    def update(self, voice_id: str, updates: dict[str, Any]) -> dict | None:
        invalid = set(updates) - self._ALLOWED_UPDATE_COLUMNS
        if invalid:
            raise ValueError(f"Invalid update columns: {invalid}")

        now = datetime.now(UTC).isoformat()
        updates["updated_at"] = now

        sql_updates = ", ".join([f"{k} = ?" for k in updates])
        params = list(updates.values())
        params.append(voice_id)

        with self._get_conn() as conn:
            conn.execute(f"UPDATE voices SET {sql_updates} WHERE voice_id = ?", params)  # noqa: S608
            conn.commit()
        return self.get_by_id(voice_id)

    def delete(self, voice_id: str) -> bool:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM voices WHERE voice_id = ?", (voice_id,))
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError as e:
                logger.debug(f"FTS rebuild skipped (table may not exist): {e}")
            conn.commit()
        return True
