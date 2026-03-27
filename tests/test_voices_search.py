import sqlite3
import importlib.util
from pathlib import Path


import sys

# Prepare a lightweight 'services' package and ensure default_voices is importable
spec = importlib.util.spec_from_loader("services", loader=None)
assert spec is not None
pkg_mod = importlib.util.module_from_spec(spec)
sys.modules["services"] = pkg_mod
dv_path = Path(__file__).resolve().parents[1] / "src" / "services" / "default_voices.py"
dv_spec = importlib.util.spec_from_file_location("services.default_voices", str(dv_path))
assert dv_spec is not None and dv_spec.loader is not None
dv_mod = importlib.util.module_from_spec(dv_spec)
dv_spec.loader.exec_module(dv_mod)
sys.modules["services.default_voices"] = dv_mod
setattr(pkg_mod, "default_voices", dv_mod)


def _load_voice_service_module():
    svc_path = Path(__file__).resolve().parents[1] / "src" / "services" / "voice_service.py"
    spec = importlib.util.spec_from_file_location("voice_service_mod", str(svc_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load voice_service module spec")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_get_top_instruct_terms_and_search(tmp_path, monkeypatch):
    # Use a temporary DB copy to avoid modifying real resources
    db = tmp_path / "quisy-tts.db"
    # create a minimal voices table
    conn = sqlite3.connect(str(db))
    conn.execute(
        """
        CREATE TABLE voices (
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
    )
    now = "2020-01-01T00:00:00Z"
    conn.execute(
        "INSERT INTO voices (id,name,example_text,instruct,language,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        ("v1", "Vo1", "Hallo Welt", "charismatic warm voice", "german", now, now),
    )
    conn.execute(
        "INSERT INTO voices (id,name,example_text,instruct,language,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        ("v2", "Vo2", "Guten Tag", "calm informative", "german", now, now),
    )
    # Insert a dummy default voice so the service does not auto-seed defaults
    conn.execute(
        "INSERT INTO voices (id,name,example_text,instruct,language,is_default,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
        ("default_000", "SeedGuard", "Seed guard", "guard", "german", 1, now, now),
    )
    conn.commit()
    conn.close()

    # monkeypatch settings to point VoiceService to this DB
    from src.config import ProjectConfig

    # Ensure VoiceService uses our temporary DB path

    settings = ProjectConfig.get_settings()
    monkeypatch.setattr(settings, "RESOURCES_DIR", tmp_path)

    # Load a fresh voice_service module using the helper to avoid package import side-effects
    vs_mod = _load_voice_service_module()
    svc = vs_mod.VoiceService(db_path=db)
    terms = svc.get_top_instruct_terms()
    assert any(t["term"] == "charismatic" or t["term"] == "calm" for t in terms)

    # search by term
    res = svc.search(["charismatic"], None)
    assert len(res) == 1 and res[0]["id"] == "v1"

    # free text search
    res2 = svc.search([], "Guten")
    assert len(res2) == 1 and res2[0]["id"] == "v2"
