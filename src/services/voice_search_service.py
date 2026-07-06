import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger("project")


class VoiceSearchService:
    """Service for searching voices using FTS5."""

    _ALLOWED_ORDER_COLUMNS = frozenset({"name", "voice_id", "created_at", "updated_at"})

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        return dict(row)

    def get_top_instruct_terms(self) -> list[dict]:
        with self._get_conn() as conn:
            try:
                rows = conn.execute("SELECT instruct FROM voices WHERE instruct IS NOT NULL").fetchall()
                import re
                from collections import Counter

                counter: Counter[str] = Counter()
                for r in rows:
                    text = r[0] or ""
                    tokens = re.findall(r"\b\w{3,}\b", text.lower(), flags=re.UNICODE)
                    counter.update(tokens)

                top = counter.most_common(50)
                return [{"term": t, "count": c} for t, c in top]
            except sqlite3.Error as e:
                logger.warning(f"Failed to retrieve instruct terms: {e}")
                return []

    def search(self, terms: list[str], q: str | None, limit: int = 20, offset: int = 0) -> list[dict]:
        with self._get_conn() as conn:
            try:
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voices_fts'")
                if cur.fetchone():
                    clauses: list[str] = []
                    params: list[str] = []
                    if terms:
                        match_expr = " AND ".join(terms)
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(match_expr)
                    if q:
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(q + "*")

                    where = " AND ".join(clauses) if clauses else "1=1"
                    sql = f"SELECT * FROM voices WHERE {where} ORDER BY name ASC LIMIT ? OFFSET ?"  # noqa: S608
                    params.extend([str(limit), str(offset)])
                    rows = conn.execute(sql, params).fetchall()
                    return [self._row_to_dict(r) for r in rows]
            except sqlite3.Error as e:
                logger.warning(f"FTS5 search failed, falling back to LIKE: {e}")

            fallback_params: list[str] = []
            parts: list[str] = []
            for t in terms:
                parts.append("instruct LIKE ?")
                fallback_params.append(f"%{t}%")
            if q:
                parts.append("(name LIKE ? OR instruct LIKE ? OR example_text LIKE ?)")
                fallback_params.extend([f"%{q}%"] * 3)

            where = " AND ".join(parts) if parts else "1=1"
            sql = f"SELECT * FROM voices WHERE {where} ORDER BY name ASC LIMIT ? OFFSET ?"  # noqa: S608
            fallback_params.extend([str(limit), str(offset)])
            rows = conn.execute(sql, fallback_params).fetchall()
            return [self._row_to_dict(r) for r in rows]
