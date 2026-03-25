"""Tests for persisting and retrieving the per-voice `system_prompt`."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure src is importable like other tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Tests run in CI/local dev environments where required env vars may be absent.
# Set minimal env vars here so ProjectConfig can initialize during imports.
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
from starlette import status


def test_create_update_get_voice_roundtrip() -> None:
    """Create a voice with system_prompt, update it, and verify round-trip via API."""
    client = TestClient(app)

    # Create voice
    payload = {
        "name": "test-voice-system-prompt",
        "example_text": "Hallo Welt",
        "system_prompt": "You are a friendly assistant who speaks clearly.",
    }

    resp = client.post("/api/voices", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()
    vid = data["id"]
    assert data["system_prompt"] == payload["system_prompt"]

    # Get voice
    resp = client.get(f"/api/voices/{vid}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["system_prompt"] == payload["system_prompt"]

    # Update system_prompt
    update_payload = {"system_prompt": "Now you are concise and professional."}
    resp = client.put(f"/api/voices/{vid}", json=update_payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    assert resp.json()["system_prompt"] == update_payload["system_prompt"]

    # Final get
    resp = client.get(f"/api/voices/{vid}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["system_prompt"] == update_payload["system_prompt"]
