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


def test_status_endpoint(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_voice_design_17b(client):
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
