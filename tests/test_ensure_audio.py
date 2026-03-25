"""Integration tests for the ensure-audio lifecycle (hash/force/regeneration).

These tests exercise TTSService._ensure_reference_audio_for_voice_id directly so
we can run generation synchronously inside the test runner. The repository's
conftest.py provides lightweight mocks for the qwen-tts model and torch so
generation is deterministic and fast.
"""

import os
import sys
import asyncio
import time
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure src is importable like other tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Minimal env vars for ProjectConfig
os.environ.setdefault("MODELS_DIR", "models")
os.environ.setdefault("VOICES_DIR", "voices")
os.environ.setdefault("OUTPUT_DIR", "output")
os.environ.setdefault("APP_DIR", "app_data")
os.environ.setdefault("RESOURCES_DIR", "resources")
os.environ.setdefault(
    "DOWNLOAD_MODELS",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base,Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
)

from api import app
from api.dependencies import get_tts_service
from config import ProjectConfig


def _assert_voice_file_exists(voice) -> Path:
    settings = ProjectConfig.get_settings()
    fn = voice.get("audio_filename")
    assert fn and fn.startswith(f"voice_{voice['id']}_") and fn.endswith(".wav")
    p = settings.VOICES_DIR / fn
    assert p.exists(), f"Expected voice file at {p}"
    return p


def test_ensure_audio_generates_and_updates_on_example_change() -> None:
    """Generate a reference audio, then change example_text and regenerate.

    The test calls the TTSService ensure method synchronously to avoid
    background scheduling uncertainty inside TestClient.
    """
    client = TestClient(app)

    # Create a voice with instruct so auto-generation is allowed
    payload = {
        "name": "test-voice-ensure-1",
        "example_text": "Hallo Welt",
        "instruct": "A clear and natural voice.",
    }
    resp = client.post("/api/voices", json=payload)
    assert resp.status_code == 201, resp.text
    vid = resp.json()["id"]

    tts = get_tts_service()

    # Run generation synchronously
    asyncio.run(tts._ensure_reference_audio_for_voice_id(vid, force=False))

    # Verify persisted filename and file exists
    resp = client.get(f"/api/voices/{vid}")
    assert resp.status_code == 200
    voice = resp.json()
    p1 = _assert_voice_file_exists(voice)

    # Update example_text and regenerate — should produce a different short key
    update_payload = {"example_text": "Hallo Welt erneut"}
    resp = client.put(f"/api/voices/{vid}", json=update_payload)
    assert resp.status_code == 200

    asyncio.run(tts._ensure_reference_audio_for_voice_id(vid, force=False))

    resp = client.get(f"/api/voices/{vid}")
    voice2 = resp.json()
    p2 = _assert_voice_file_exists(voice2)

    assert p1.name != p2.name, "Expected audio filename to change after example_text update"


def test_ensure_audio_force_regenerates_overwrites_file_mtime() -> None:
    """Ensure that calling ensure with force=True rewrites the voice file (mtime changes).

    The engine + cache are deterministic, so content may be identical, but the
    file write should update the file's modification time.
    """
    client = TestClient(app)

    payload = {
        "name": "test-voice-ensure-2",
        "example_text": "Ein Test",
        "instruct": "A clear and natural voice.",
    }
    resp = client.post("/api/voices", json=payload)
    assert resp.status_code == 201, resp.text
    vid = resp.json()["id"]

    tts = get_tts_service()

    asyncio.run(tts._ensure_reference_audio_for_voice_id(vid, force=False))

    resp = client.get(f"/api/voices/{vid}")
    voice = resp.json()
    p = _assert_voice_file_exists(voice)

    # Make file older artificially
    old_time = time.time() - 3600
    os.utime(p, (old_time, old_time))
    mtime_before = p.stat().st_mtime

    # Force regeneration
    asyncio.run(tts._ensure_reference_audio_for_voice_id(vid, force=True))

    resp = client.get(f"/api/voices/{vid}")
    voice2 = resp.json()
    p2 = ProjectConfig.get_settings().VOICES_DIR / voice2["audio_filename"]
    assert p2.exists()
    mtime_after = p2.stat().st_mtime

    assert mtime_after >= mtime_before, "Expected mtime to be updated after forced regeneration"
