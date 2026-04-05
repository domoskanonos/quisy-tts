import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from api.app import app
from api.dependencies import get_voice_service, get_tts_service
from pathlib import Path
from datetime import datetime

# Setup mock dependencies
mock_voice_service = MagicMock()
mock_tts_service = MagicMock()

# Override dependencies
app.dependency_overrides[get_voice_service] = lambda: mock_voice_service
app.dependency_overrides[get_tts_service] = lambda: mock_tts_service

client = TestClient(app)


def create_mock_voice(voice_id="v1", name="Voice 1"):
    return {
        "voice_id": voice_id,
        "name": name,
        "example_text": "example",
        "instruct": "instruct",
        "language": "german",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


def test_list_voices_success():
    mock_voice_service.list_voices.return_value = [create_mock_voice()]

    response = client.get("/api/voices/")

    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert data["total"] == 1
    assert data["voices"][0]["voice_id"] == "v1"


def test_get_voice_success():
    mock_voice_service.get_voice.return_value = create_mock_voice("test-voice")

    response = client.get("/api/voices/test-voice")

    assert response.status_code == 200
    assert response.json()["voice_id"] == "test-voice"


def test_get_voice_invalid_pattern():
    response = client.get("/api/voices/invalid@id")
    assert response.status_code == 422  # FastAPI validation error for Path pattern


def test_get_voice_not_found():
    mock_voice_service.get_voice.return_value = None
    response = client.get("/api/voices/missing")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_voice_success():
    mock_voice_service.create_voice.return_value = create_mock_voice("new-voice")
    mock_tts_service.generate_audio = AsyncMock(return_value=Path("dummy.wav"))

    # Mock reading bytes and unlinking
    with patch("pathlib.Path.read_bytes", return_value=b"audio data"), patch("pathlib.Path.unlink"):
        response = client.post(
            "/api/voices/",
            json={"voice_id": "new-voice", "text": "Hello world", "instruct": "Calm voice", "language": "english"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_voice_service.set_audio.assert_called_once()


def test_delete_voice_success():
    mock_voice_service.get_voice.return_value = create_mock_voice("test-voice")
    mock_voice_service.delete_voice.return_value = True

    response = client.delete("/api/voices/test-voice")

    assert response.status_code == 204


def test_delete_voice_not_found():
    mock_voice_service.get_voice.return_value = None
    response = client.delete("/api/voices/nonexistent")
    assert response.status_code == 404
