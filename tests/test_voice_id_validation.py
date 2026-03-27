import sys
from pathlib import Path


def _client():
    sys.path.insert(0, str(Path("src").resolve()))
    from fastapi.testclient import TestClient

    from api.app import app

    return TestClient(app)


def test_invalid_id_get_returns_422():
    client = _client()
    r = client.get("/api/voices/UPPERCASE")
    assert r.status_code == 422
    assert "string_pattern_mismatch" in r.text or "String should match pattern" in r.text


def test_invalid_id_put_returns_422():
    client = _client()
    payload = {"name": "x", "example_text": "y"}
    r = client.put("/api/voices/UPPERCASE", json=payload)
    assert r.status_code == 422


def test_invalid_id_post_audio_returns_422():
    client = _client()
    files = {"file": ("f.wav", b"\x00\x01", "audio/wav")}
    r = client.post("/api/voices/UPPERCASE/audio", files=files)
    # Pattern mismatch yields 422 from FastAPI path validation
    assert r.status_code == 422
