import sqlite3
from pathlib import Path

from src.domain.voice.models import Voice


def test_db_schema_vs_model_consistency(tmp_path: Path):
    """Verify that a voices table schema matches the Voice model attributes."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE voices (
            voice_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            example_text TEXT NOT NULL,
            instruct TEXT,
            language TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(voices)")
    columns_info = cursor.fetchall()
    conn.close()

    db_columns = {col[1] for col in columns_info}

    import dataclasses

    model_fields = {field.name for field in dataclasses.fields(Voice)}

    assert model_fields.issubset(db_columns), f"Model fields missing in DB: {model_fields - db_columns}"
    assert db_columns.issubset(model_fields), f"DB columns missing in Model: {db_columns - model_fields}"
    assert "voice_id" in db_columns
    assert "name" in db_columns
