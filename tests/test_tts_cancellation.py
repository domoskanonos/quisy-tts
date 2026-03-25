"""Tests for TTSService cancellation and forced regeneration behavior.

These tests simulate a long-running `generate_audio` by patching the
TTSService instance method to await on asyncio.Events so we can trigger
cancellation and verify the running task is cancelled and a new forced
generation is started.
"""

import os
import sys
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Minimal env vars for ProjectConfig before importing application modules
os.environ.setdefault("MODELS_DIR", "models")
os.environ.setdefault("VOICES_DIR", "voices")
os.environ.setdefault("OUTPUT_DIR", "output")
os.environ.setdefault("APP_DIR", "app_data")
os.environ.setdefault("RESOURCES_DIR", "resources")
os.environ.setdefault(
    "DOWNLOAD_MODELS",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base,Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
)

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from api import app
from api.dependencies import get_tts_service
from config import ProjectConfig


@pytest.mark.asyncio
async def test_force_cancel_restarts_generation() -> None:
    client = TestClient(app)

    # Create voice
    payload = {
        "name": "test-cancel-voice",
        "example_text": "Cancel me",
        "instruct": "A clear and natural voice.",
    }
    resp = client.post("/api/voices", json=payload)
    assert resp.status_code == 201
    vid = resp.json()["id"]

    tts = get_tts_service()
    settings = ProjectConfig.get_settings()

    # Events to coordinate between calls
    first_started = asyncio.Event()
    first_cancelled = asyncio.Event()
    first_block = asyncio.Event()
    second_started = asyncio.Event()

    calls = {"n": 0}

    async def fake_generate_audio(
        self, text, language, mode, model_size, reference_audio=None, ref_text=None, instruct=None, speaker=None
    ):
        # Simulate a long-running first call which will be cancelled, then a quick second call
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            first_started.set()
            try:
                await first_block.wait()
            except asyncio.CancelledError:
                # Signal cancellation and re-raise so the task records CancelledError
                first_cancelled.set()
                raise
            # If not cancelled, create a file and return its path
            out = settings.OUTPUT_DIR / "cache_first.wav"
            out.write_bytes(b"first")
            return out
        else:
            second_started.set()
            out = settings.OUTPUT_DIR / "cache_second.wav"
            out.write_bytes(b"second")
            return out

    # Bind the fake to this TTSService instance
    import types

    setattr(tts, "generate_audio", types.MethodType(fake_generate_audio, tts))

    # Trigger first generation (background)
    tts.trigger_reference_audio_generation(vid, force=False)

    # Wait until the fake generate started
    await asyncio.wait_for(first_started.wait(), timeout=5.0)

    # Capture the running task
    old_task = tts._ref_gen_tasks.get(vid)
    assert old_task is not None and not old_task.done()

    # Now trigger forced regeneration which should cancel the old task and start a new one
    tts.trigger_reference_audio_generation(vid, force=True)

    new_task = tts._ref_gen_tasks.get(vid)
    assert new_task is not None and new_task is not old_task

    # Wait for cancellation to be observed
    await asyncio.wait_for(first_cancelled.wait(), timeout=5.0)

    # Allow second generation to complete (the fake returns quickly)
    # also set the first_block to release if cancellation didn't occur yet
    first_block.set()

    # Wait until second started and task completes
    await asyncio.wait_for(second_started.wait(), timeout=5.0)

    # Poll status until done or timeout
    for _ in range(50):
        status = tts.get_reference_generation_status(vid)
        if status.get("status") == "done":
            break
        await asyncio.sleep(0.1)

    assert tts.get_reference_generation_status(vid).get("status") == "done"

    # Verify the voice entry now points to a generated file (the second key)
    # The short key is part of the filename; ensure a voice file exists
    from fastapi.testclient import TestClient as _TC

    c = _TC(app)
    resp = c.get(f"/api/voices/{vid}")
    assert resp.status_code == 200
    voice = resp.json()
    fn = voice.get("audio_filename")
    assert fn and fn.startswith(f"voice_{vid}_") and fn.endswith(".wav")
