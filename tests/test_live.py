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
    return httpx.Client(base_url=live_server, timeout=60.0)  # Increased client timeout


def test_info_endpoints(client):
    """
    Test the info endpoints:
    1. Verify status endpoint.
    2. Verify languages endpoint returns a list of ISO 639-1 codes.
    """
    # 1. Status
    response = client.get("/api/")
    assert response.status_code == 200
    assert "message" in response.json()

    # 2. Languages
    response = client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert "de" in data["languages"]
    assert "en" in data["languages"]
    # Ensure full names are supported for mapping
    assert "german" in data["languages"]


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
        "language": payload["language"],
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
