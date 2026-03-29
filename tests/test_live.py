import json
import pytest
import uvicorn
import threading
import time
import httpx
import sys
from pathlib import Path

# Add src to sys.path so we can import the app
src_dir = str(Path(__file__).resolve().parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from api.app import app

# Port for the test server
TEST_PORT = 8046


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=TEST_PORT, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def live_server():
    # Start the server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for the server to be ready
    base_url = f"http://127.0.0.1:{TEST_PORT}"
    client = httpx.Client(base_url=base_url)

    for _ in range(60):  # Increased timeout for initial model load
        try:
            client.get("/api/")
            break
        except httpx.ConnectError:
            time.sleep(0.5)
    else:
        pytest.fail("Server did not start in time")

    yield base_url
    client.close()


@pytest.fixture(scope="session")
def client(live_server):
    return httpx.Client(base_url=live_server, timeout=120.0)


def test_status_endpoint(client):
    """
    Test the root status endpoint to ensure the API server is up and responding.
    """
    response = client.get("/api/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_voice_design_17b(client):
    """
    Test the Voice Design generation endpoint:
    1. Creates a new voice entry using the provided payload.
    2. Triggers audio generation for the new voice.
    3. Verifies that the voice is successfully created (status: success).
    """
    payload_path = Path(__file__).parent / "resources" / "voice_design_payload.json"
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # New payload: voice_id, instruct, language, text
    new_payload = {
        "voice_id": "test_voice",
        "instruct": payload["instruct"],
        "language": "german",  # Updated to full name
        "text": payload["text"],
    }

    response = client.post("/api/voices/", json=new_payload, timeout=120.0)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "voice_id" in response.json()


def test_audio_upload(client):
    """
    Test the audio upload endpoint:
    1. Uploads a dummy WAV file.
    2. Verifies that the API returns a valid public URL for the uploaded file.
    3. Downloads the file from the returned URL and verifies its integrity (size match).
    """
    # Create a small dummy WAV file
    test_wav = Path(__file__).parent / "resources" / "testaudio.wav"

    with open(test_wav, "rb") as f:
        files = {"file": ("testaudio.wav", f, "audio/wav")}
        response = client.post("/api/audio/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "url" in data

    # Verify we can download it
    url = data["url"]

    # Extract the path part of the URL to download it
    from urllib.parse import urlparse

    parsed = urlparse(url)
    download_url = parsed.path

    # Use the live_server client to download
    response_download = client.get(download_url)
    assert response_download.status_code == 200
    assert len(response_download.content) == test_wav.stat().st_size


def test_audio_concatenate(client):
    """
    Test the audio concatenation endpoint:
    1. Upload two audio files.
    2. Request concatenation of these files.
    3. Verify that the API returns a URL to the new concatenated file.
    4. Download the file from the URL and verify it exists.
    """
    test_wav = Path(__file__).parent / "resources" / "testaudio.wav"

    # 1. Upload two files
    filenames = []
    for _ in range(2):
        with open(test_wav, "rb") as f:
            files = {"file": ("testaudio.wav", f, "audio/wav")}
            response = client.post("/api/audio/upload", files=files)
            assert response.status_code == 200
            url = response.json()["url"]
            filename = url.split("/")[-1]
            filenames.append(filename)

    # 2. Concatenate
    payload = {"audio_files": filenames}
    response = client.post("/api/audio/concatenate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "url" in data

    # 3. Verify download
    from urllib.parse import urlparse

    parsed = urlparse(data["url"])
    download_url = parsed.path

    # Use the live_server client to download
    response_download = client.get(download_url)
    assert response_download.status_code == 200
    assert len(response_download.content) > 0


def test_voice_management_lifecycle(client):
    """
    Test the Voice Management lifecycle:
    1. List voices and pick the first one.
    2. Generate text-to-speech using that voice.
    3. Generate audio using SSML.
    4. Delete the reference audio of that voice.
    5. Generate text-to-speech again (should re-create/ensure audio).
    6. Perform same operations for a newly created voice.
    """
    # 1. List voices
    response = client.get("/api/voices/")
    assert response.status_code == 200
    voices = response.json()["voices"]
    assert len(voices) > 0

    # Filter for a non-default voice to test deletion, or just use a custom created one
    # For now, let's just pick one.
    voice = voices[0]
    voice_id = voice["voice_id"]

    # 2. Generate text (make sure it's a voice with audio)
    # If the default voice is missing its audio file, this will fail.
    # We should ensure the voice has audio first.
    # Upload dummy audio if missing
    # In the new structure, we don't check for audio_filename.
    # Just assume ensure_audio handles it.

    payload = {"text": "Das ist ein Test.", "language": "de", "voice_id": voice_id}
    response = client.post("/api/generate/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/wav"

    # 3. Generate SSML
    ssml_path = Path(__file__).parent / "resources" / "test_ssml.xml"
    with open(ssml_path, "r", encoding="utf-8") as f:
        ssml_content = f.read()
    response = client.post("/api/generate/ssml", content=ssml_content)
    assert response.status_code == 200
    assert "url" in response.json()

    # 4. Delete reference audio
    from services.voice_service import VoiceService

    vs = VoiceService()
    # The new path logic
    audio_path = vs._voices_dir / f"voice_{voice_id}.wav"
    if audio_path.exists():
        audio_path.unlink()

    # 5. Generate text again
    response = client.post("/api/generate/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/wav"

    # 6. Same with a newly created voice
    new_voice_payload = {
        "voice_id": "new_test_voice",
        "instruct": "A friendly female voice.",
        "language": "de",
        "text": "Das ist eine neue Stimme.",
    }
    response = client.post("/api/voices/", json=new_voice_payload)
    assert response.status_code == 200
    assert response.json()["voice_id"] == "new_test_voice"

    # Generate text for new voice
    payload["voice_id"] = "new_test_voice"
    response = client.post("/api/generate/generate", json=payload)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/wav"

    # Cleanup: delete the newly created voice
    response = client.delete(f"/api/voices/new_test_voice")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/api/voices/new_test_voice")
    assert response.status_code == 404
