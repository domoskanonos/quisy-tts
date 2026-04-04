import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from api.app import app
from api.dependencies import get_tts_service, get_cleanup_service, get_voice_service

# Setup mock dependencies
mock_tts_service = MagicMock()
# IMPORTANT: FileResponse needs an absolute path to an existing file
test_audio_path = Path.cwd() / "test.wav"
mock_tts_service.generate_audio = AsyncMock(return_value=test_audio_path)
# Need to mock voice_audio_integrity to avoid errors
mock_tts_service.voice_audio_integrity = MagicMock()
mock_tts_service.voice_audio_integrity.ensure_audio = AsyncMock()

mock_cleanup_service = MagicMock()
mock_voice_service = MagicMock()

# Override dependencies
app.dependency_overrides[get_tts_service] = lambda: mock_tts_service
app.dependency_overrides[get_cleanup_service] = lambda: mock_cleanup_service
app.dependency_overrides[get_voice_service] = lambda: mock_voice_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def create_dummy_audio():
    test_audio_path.write_text("dummy")
    yield
    test_audio_path.unlink(missing_ok=True)


def test_generate_audio_endpoint():

    # Setup mock for voice existence
    mock_voice_service.get_voice.return_value = {"id": "test_voice"}

    # Test request
    response = client.post("/api/generate/generate", json={"text": "Hello", "language": "en", "voice_id": "test_voice"})

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/wav"
    mock_tts_service.generate_audio.assert_called_once()


def test_generate_audio_voice_not_found():
    # Setup mock for voice missing
    mock_voice_service.get_voice.return_value = None

    response = client.post(
        "/api/generate/generate", json={"text": "Hello", "language": "en", "voice_id": "nonexistent"}
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
