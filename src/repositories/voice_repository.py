import sqlite3
from pathlib import Path
from datetime import UTC, datetime
from typing import Any
from config import ProjectConfig
from schemas.languages import resolve_language

logger = ProjectConfig.get_logger()


class VoiceRepository:
    """Repository for CRUD operations on voice metadata."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
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
            """)
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        cursor = conn.execute("PRAGMA table_info(voices)")
        columns = {row[1]: row for row in cursor.fetchall()}
        if "voice_name" not in columns:
            if "description" in columns:
                conn.execute("ALTER TABLE voices RENAME COLUMN description TO voice_name")
            else:
                conn.execute("ALTER TABLE voices ADD COLUMN voice_name TEXT")
            conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        data = {
            "voice_id": row["voice_id"],
            "name": row["name"],
            "example_text": row["example_text"],
            "instruct": row["instruct"],
            "language": row["language"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        if "voice_name" in row.keys():
            data["voice_name"] = row["voice_name"]
        else:
            data["voice_name"] = None
        return data

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

    def create(
        self, voice_id: str, name: str, example_text: str, instruct: str | None, voice_name: str | None, language: str
    ) -> dict | None:
        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO voices (voice_id, name, example_text, instruct, voice_name, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (voice_id, name, example_text, instruct, voice_name, resolve_language(language), now, now),
            )
            # Rebuild FTS if it exists
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError:
                pass
            conn.commit()
        return self.get_by_id(voice_id)

    def update(self, voice_id: str, updates: dict[str, Any]) -> dict | None:
        now = datetime.now(UTC).isoformat()
        updates["updated_at"] = now

        sql_updates = ", ".join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values())
        params.append(voice_id)

        with self._get_conn() as conn:
            conn.execute(f"UPDATE voices SET {sql_updates} WHERE voice_id = ?", params)
            conn.commit()
        return self.get_by_id(voice_id)

    def delete(self, voice_id: str) -> bool:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM voices WHERE voice_id = ?", (voice_id,))
            # Rebuild FTS if it exists
            try:
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
            except sqlite3.OperationalError:
                pass
            conn.commit()
        return True
