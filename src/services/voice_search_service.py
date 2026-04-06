import sqlite3
from pathlib import Path


class VoiceSearchService:
    """Service for searching voices using FTS5."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        data = dict(row)
        return data

    def get_top_instruct_terms(self) -> list[dict]:
        with self._get_conn() as conn:
            try:
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
        with self._get_conn() as conn:
            try:
                # Prefer FTS5 if available
                cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='voices_fts'")
                if cur.fetchone():
                    clauses = []
                    params: list[str] = []
                    if terms:
                        match_expr = " AND ".join([t for t in terms])
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(match_expr)
                    if q:
                        clauses.append("rowid IN (SELECT rowid FROM voices_fts WHERE voices_fts MATCH ?)")
                        params.append(q + "*")

                    where = " AND ".join(clauses) if clauses else "1=1"
                    sql = f"SELECT * FROM voices WHERE {where} ORDER BY name ASC LIMIT ? OFFSET ?"
                    params.extend([str(limit), str(offset)])
                    rows = conn.execute(sql, params).fetchall()
                    return [self._row_to_dict(r) for r in rows]
            except Exception:
                pass

            # Fallback
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
