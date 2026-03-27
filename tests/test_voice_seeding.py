import sqlite3


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
    import importlib

    config = importlib.import_module("config")

    config.ProjectConfig._settings = None
    config.ProjectConfig._logger = None

    # Create an empty resources DB file (VoiceService expects the file to exist).
    db_path = tmp_path / "quisy-tts.db"
    conn = sqlite3.connect(str(db_path))
    conn.commit()
    conn.close()

    # Determine expected count from the default_voices data by loading the
    # module directly from the source file to avoid importing the 'services'
    # package (which would run package-level imports and cause circular
    # import failures in this test environment).
    from pathlib import Path
    import importlib.util

    dv_path = Path(__file__).resolve().parents[1] / "src" / "services" / "default_voices.py"
    dv_spec = importlib.util.spec_from_file_location("services.default_voices", str(dv_path))
    assert dv_spec is not None and dv_spec.loader is not None
    dv_mod = importlib.util.module_from_spec(dv_spec)
    dv_spec.loader.exec_module(dv_mod)
    expected = len(dv_mod.DEFAULT_VOICES)

    # Load the voice_service module directly from file and instantiate using
    # our temporary DB so DB initialization runs in isolation.
    svc_path = Path(__file__).resolve().parents[1] / "src" / "services" / "voice_service.py"
    svc_spec = importlib.util.spec_from_file_location("voice_service_mod", str(svc_path))
    assert svc_spec is not None and svc_spec.loader is not None
    vs_mod = importlib.util.module_from_spec(svc_spec)
    svc_spec.loader.exec_module(vs_mod)
    _ = vs_mod.VoiceService(db_path=db_path)

    # Verify the DB was seeded with the expected number of default voices
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM voices WHERE is_default = 1")
    count = cur.fetchone()[0]
    conn.close()

    assert count == expected, f"expected {expected} default voices, got {count}"
