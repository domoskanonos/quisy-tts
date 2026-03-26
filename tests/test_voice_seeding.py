import importlib
import sqlite3
from pathlib import Path


def test_seeds_default_voices(tmp_path, monkeypatch):
    """Ensure VoiceService seeds DEFAULT_VOICES into an empty resources DB.

    This reproduces the runtime path that previously raised a NameError when a
    module-level log referenced `DEFAULT_VOICES` before it was imported.
    """
    # Provide required environment variables before importing config/voice modules
    required = [
        "MODELS_DIR",
        "VOICES_DIR",
        "OUTPUT_DIR",
        "APP_DIR",
        "RESOURCES_DIR",
        "DOWNLOAD_MODELS",
    ]
    for k in required:
        monkeypatch.setenv(k, str(tmp_path / k.lower()))

    # Reset cached ProjectConfig state if present so imports re-evaluate env.
    import config

    config.ProjectConfig._settings = None
    config.ProjectConfig._logger = None

    # Create an empty resources DB file (VoiceService expects the file to exist).
    db_path = tmp_path / "quisy-tts.db"
    conn = sqlite3.connect(str(db_path))
    conn.commit()
    conn.close()

    # Determine expected count from the default_voices data
    dv = importlib.import_module("services.default_voices")
    expected = len(dv.DEFAULT_VOICES)

    # Import the service module (now that env is set) and instantiate using our DB
    vs_mod = importlib.import_module("services.voice_service")

    svc = vs_mod.VoiceService(db_path=db_path)

    # Verify the DB was seeded with the expected number of default voices
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM voices WHERE is_default = 1")
    count = cur.fetchone()[0]
    conn.close()

    assert count == expected, f"expected {expected} default voices, got {count}"
