"""Voice management service – CRUD operations with SQLite persistence."""

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from config import ProjectConfig

# NOTE: default voices are imported lazily inside _seed_defaults to avoid
# package-level circular imports during test-time module loading.
from schemas.languages import resolve_language

logger = ProjectConfig.get_logger()


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

    def __init__(self, voices_dir: Path | None = None, db_path: Path | None = None) -> None:
        settings = ProjectConfig.get_settings()
        self._voices_dir = voices_dir or settings.VOICES_DIR
        print(f"DEBUG: VoiceService init. voices_dir={self._voices_dir}, CWD={Path.cwd()}")
        self._voices_dir.mkdir(parents=True, exist_ok=True)

        # Use either provided db_path (useful for tests) or resources DB as the
        # single authoritative, writable runtime DB.
        self._db_path = Path(db_path) if db_path is not None else settings.RESOURCES_DIR / "quisy-tts.db"

        if not self._db_path.exists():
            # If the DB doesn't exist we try to create an empty DB file. In
            # production a missing DB is a configuration error, but tests and
            # some runtime paths expect to be able to create a fresh DB.
            try:
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                import sqlite3 as _sqlite

                conn = _sqlite.connect(str(self._db_path))
                conn.commit()
                conn.close()
                logger.info(f"Created new resources DB at {self._db_path}")
            except Exception as e:
                logger.error(f"resources DB not found at {self._db_path}")
                raise FileNotFoundError(f"resources DB not found at {self._db_path}") from e

        # Ensure we can write to the resources DB
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
        """Create table, run migrations, and seed default voices if empty."""
        with self._get_conn() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            self._migrate(conn)

            # Check if default voices already exist
            count = conn.execute("SELECT COUNT(*) FROM voices WHERE is_default = 1").fetchone()[0]

            if count == 0:
                self._seed_defaults(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Run schema migrations for existing databases."""
        # Check if 'language' column exists
        columns = {row[1] for row in conn.execute("PRAGMA table_info(voices)").fetchall()}
        if "language" not in columns:
            logger.info("Migrating voices table: adding 'language' column...")
            conn.execute("ALTER TABLE voices ADD COLUMN language TEXT NOT NULL DEFAULT 'german'")
            conn.commit()

        # No-op: system_prompt removed from schema

        # Normalize existing language values to canonical form (resolve_language)
        try:
            rows = conn.execute("SELECT id, language FROM voices").fetchall()
            for r in rows:
                vid = r[0]
                lang = (r[1] or "").strip()
                if not lang:
                    continue
                resolved = resolve_language(lang)
                if resolved != lang.lower():
                    logger.info(f"Normalizing language for voice {vid}: '{lang}' -> '{resolved}'")
                    conn.execute("UPDATE voices SET language = ? WHERE id = ?", (resolved, vid))
            conn.commit()
        except Exception as e:
            logger.warning(f"Failed to normalize voice languages during migration: {e}")

        # Ensure FTS5 virtual table for full-text search exists and is synced.
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voices_fts'")
            if cur.fetchone() is None:
                logger.info("Creating FTS5 virtual table 'voices_fts' for full-text search...")
                # Use content='voices' so we don't duplicate storage; content_rowid maps to voices.rowid
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS voices_fts USING fts5(name, instruct, example_text, content='voices', content_rowid='rowid', tokenize='unicode61')"
                )
                # Rebuild index from existing voices
                conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")

                # Triggers to keep the FTS index in sync
                conn.execute(
                    "CREATE TRIGGER IF NOT EXISTS voices_ai AFTER INSERT ON voices BEGIN "
                    "INSERT INTO voices_fts(rowid, name, instruct, example_text) VALUES (new.rowid, new.name, new.instruct, new.example_text); END;"
                )
                conn.execute(
                    "CREATE TRIGGER IF NOT EXISTS voices_ad AFTER DELETE ON voices BEGIN "
                    "DELETE FROM voices_fts WHERE rowid = old.rowid; END;"
                )
                conn.execute(
                    "CREATE TRIGGER IF NOT EXISTS voices_au AFTER UPDATE ON voices BEGIN "
                    "UPDATE voices_fts SET name = new.name, instruct = new.instruct, example_text = new.example_text WHERE rowid = old.rowid; END;"
                )
                conn.commit()
        except Exception as e:
            # FTS5 may not be available in the SQLite build; warn but continue.
            logger.warning(f"Failed to create or initialize FTS5 table: {e}")

    def _seed_defaults(self, conn: sqlite3.Connection) -> None:
        """Insert all default voices."""
        # Import DEFAULT_VOICES lazily to avoid circular imports during tests /
        # runtime initialization. Prefer the regular package import but fall
        # back to loading the module directly from the file system if that
        # triggers an import-time circular dependency.
        try:
            import services.default_voices

            DEFAULT_VOICES = services.default_voices.DEFAULT_VOICES
        except Exception:
            from importlib import util
            from pathlib import Path

            dv_path = Path(__file__).resolve().parents[0] / "default_voices.py"
            spec = util.spec_from_file_location("services.default_voices", str(dv_path))
            if spec and spec.loader:
                dv_mod = util.module_from_spec(spec)
                spec.loader.exec_module(dv_mod)
                DEFAULT_VOICES = dv_mod.DEFAULT_VOICES
            else:
                raise ImportError("Could not load default_voices")

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
                    voice.get("instruct"),
                    voice.get("language", "german"),
                    now,
                    now,
                ),
            )

        # Log how many defaults were seeded (DEFAULT_VOICES is available here
        # because we imported it lazily above).
        try:
            logger.info(f"Seeded {len(DEFAULT_VOICES)} default voices into SQLite.")
        except Exception:
            # Logging should never break DB initialization
            pass

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
                    sql = f"SELECT * FROM voices WHERE {where} ORDER BY is_default DESC, name ASC LIMIT ? OFFSET ?"
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
            sql = f"SELECT * FROM voices WHERE {where} ORDER BY is_default DESC, name ASC LIMIT ? OFFSET ?"
            like_params.extend([str(limit), str(offset)])
            rows = conn.execute(sql, like_params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_voice(self, voice_id: str) -> dict | None:
        """Return a single voice by ID, or None if not found."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM voices WHERE id = ?", (voice_id,)).fetchone()
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
        # system_prompt: removed
        language: str = "german",
    ) -> dict | None:
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
        # get_voice may return None according to typing, but in normal flow it exists
        return self.get_voice(voice_id)

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
        # system_prompt removed from update fields

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

    def set_audio(
        self, voice_id: str, audio_data: bytes, original_filename: str, audio_filename: str | None = None
    ) -> dict | None:
        """Save or replace the audio file for a voice."""
        voice = self.get_voice(voice_id)
        if voice is None:
            return None

        # Remove old generated audio files for this voice (keep user uploads if they don't match prefix)
        try:
            for p in list(self._voices_dir.glob(f"voice_{voice_id}_*.wav")):
                # Only remove files that look like auto-generated (have a short hex suffix)
                name = p.name
                parts = name.rsplit("_", 2)
                if len(parts) >= 2 and parts[-1].lower().endswith(".wav"):
                    # e.g. voice_<id>_<short>.wav -> remove only if it's not the exact
                    # filename the user explicitly uploaded (voice_<id>.wav)
                    try:
                        p.unlink()
                        logger.info(f"Removed old generated audio file: {p.name}")
                    except Exception:
                        logger.debug(f"Failed to remove old generated audio file: {p}")
        except Exception:
            # ignore if glob/read fails
            pass

        # Determine filename to use
        if audio_filename:
            final_filename = audio_filename
        else:
            # Determine extension from original filename
            ext = Path(original_filename).suffix or ".wav"
            final_filename = f"voice_{voice_id}{ext}"

        audio_path = self._voices_dir / final_filename
        audio_path.write_bytes(audio_data)

        now = datetime.now(UTC).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE voices SET audio_filename = ?, updated_at = ? WHERE id = ?",
                (final_filename, now, voice_id),
            )

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
