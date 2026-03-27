from pathlib import Path
import sys


def _client():
    sys.path.insert(0, str(Path("src").resolve()))
    from fastapi.testclient import TestClient
    from api.app import app

    return TestClient(app)


def test_search_terms_route_present_and_returns_terms():
    client = _client()
    r = client.get("/api/voices/terms")
    assert r.status_code == 200
    data = r.json()
    assert "terms" in data


def test_post_audio_to_reserved_keyword_returns_404():
    client = _client()
    files = {"file": ("f.wav", b"\x00\x01", "audio/wav")}
    r = client.post("/api/voices/terms/audio", files=files)
    # Handler explicitly rejects reserved keywords with 404
    assert r.status_code == 404


def test_ensure_audio_reserved_keyword_returns_404():
    client = _client()
    r = client.post("/api/voices/terms/ensure-audio", data={})
    assert r.status_code == 404


def test_ensure_audio_status_reserved_keyword_returns_404():
    client = _client()
    r = client.get("/api/voices/terms/ensure-audio/status")
    assert r.status_code == 404
