import sqlite3
from src.domain.voice.models import Voice
from config import ProjectConfig


def test_db_schema_vs_model_consistency():
    """Verify that the database 'voices' table schema matches the Voice model attributes."""

    # 1. Get DB path from configuration (similar to repository)
    settings = ProjectConfig.get_settings()
    db_path = settings.APP_DIR / "quisy-tts.db"

    assert db_path.exists(), f"Database not found at {db_path}"

    # 2. Get columns from database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(voices)")
    columns_info = cursor.fetchall()
    conn.close()

    # Column name is index 1 in table_info (cid, name, type, notnull, dflt_value, pk)
    db_columns = {col[1] for col in columns_info}

    # 3. Get fields from Voice model
    # We use dataclasses.fields or just inspect __annotations__
    import dataclasses

    model_fields = {field.name for field in dataclasses.fields(Voice)}

    # 4. Check for consistency
    # Ensure all model fields exist in the database
    assert model_fields.issubset(db_columns), f"Model fields missing in DB: {model_fields - db_columns}"

    # Ensure all DB columns exist in the model
    # Note: we might have hidden/internal columns in DB not in Model,
    # but based on the requirement, they should be mapped.
    assert db_columns.issubset(model_fields), f"DB columns missing in Model: {db_columns - model_fields}"

    # Specifically check the primary identifier
    assert "voice_id" in db_columns, "voice_id column missing in DB"
    assert "name" in db_columns, "name column missing in DB"
