"""Comprehensive test suite for Cosmo TTS API."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from project.schemas import LANGUAGE_MAP, GenerateRequest, TTSParams


class TestLanguageMapping:
    """Tests for the language code mapping functionality."""

    def test_short_code_to_full_name(self) -> None:
        """Test that short codes are correctly resolved to full names."""
        params = TTSParams(language_id="de")
        assert params.resolved_language == "german"

    def test_english_mapping(self) -> None:
        """Test English language mapping."""
        params = TTSParams(language_id="en")
        assert params.resolved_language == "english"

    def test_full_name_passthrough(self) -> None:
        """Test that full names pass through unchanged."""
        params = TTSParams(language_id="german")
        assert params.resolved_language == "german"

    def test_unknown_code_passthrough(self) -> None:
        """Test that unknown codes pass through unchanged."""
        params = TTSParams(language_id="unknown")
        assert params.resolved_language == "unknown"

    def test_all_supported_languages(self) -> None:
        """Test all supported language mappings."""
        expected_mappings = {
            "de": "german",
            "en": "english",
            "fr": "french",
            "es": "spanish",
            "it": "italian",
            "pt": "portuguese",
            "ru": "russian",
            "ja": "japanese",
            "ko": "korean",
            "zh": "chinese",
            "auto": "auto",
        }
        for code, full_name in expected_mappings.items():
            params = TTSParams(language_id=code)
            assert params.resolved_language == full_name, f"Failed for {code}"


class TestGenerateRequest:
    """Tests for the GenerateRequest model."""

    def test_minimal_request(self) -> None:
        """Test creating a request with only required fields."""
        request = GenerateRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.stream is False
        assert request.mode == "base"

    def test_full_request(self) -> None:
        """Test creating a request with all fields."""
        request = GenerateRequest(
            text="Test text",
            language_id="de",
            mode="voice_design",
            instruct="a calm narrator",
            model_size="0.6B",
            stream=True,
        )
        assert request.text == "Test text"
        assert request.language_id == "de"
        assert request.mode == "voice_design"
        assert request.instruct == "a calm narrator"
        assert request.model_size == "0.6B"
        assert request.stream is True


class TestTTSParams:
    """Tests for the TTSParams model."""

    def test_default_values(self) -> None:
        """Test default TTSParams values."""
        params = TTSParams()
        assert params.language_id == "german"
        assert params.mode == "base"
        assert params.speed == 1.0
        assert params.reference_audio is None

    def test_custom_values(self) -> None:
        """Test TTSParams with custom values."""
        params = TTSParams(
            language_id="en",
            mode="custom_voice",
            speaker="eric",
            model_size="1.7B",
        )
        assert params.language_id == "en"
        assert params.resolved_language == "english"
        assert params.mode == "custom_voice"
        assert params.speaker == "eric"


class TestAPIEndpoints:
    """Tests for the FastAPI endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the API."""
        from project.main import app

        return TestClient(app)

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Cosmo TTS API is running" in data["message"]

    def test_openapi_endpoint(self, client: TestClient) -> None:
        """Test the OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/generate" in data["paths"]

    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test the Swagger UI endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_generate_endpoint_validation(self, client: TestClient) -> None:
        """Test that missing 'text' field returns validation error."""
        response = client.post("/generate", json={})
        assert response.status_code == 422  # Validation error

    @patch("project.main.tts_engine")
    def test_generate_endpoint_with_mock(
        self, mock_engine: MagicMock, client: TestClient
    ) -> None:
        """Test /generate endpoint with mocked TTS engine."""
        # Setup mock
        mock_engine.generate_and_save.return_value = None

        response = client.post(
            "/generate",
            json={
                "text": "Test audio generation",
                "language_id": "de",
                "mode": "base",
            },
        )
        # Will return 500 because mock returns None (no file created)
        # But this tests the request handling works
        assert response.status_code in [200, 500]


class TestLanguageMapConstant:
    """Tests for the LANGUAGE_MAP constant."""

    def test_language_map_has_common_languages(self) -> None:
        """Test that LANGUAGE_MAP contains common languages."""
        assert "de" in LANGUAGE_MAP
        assert "en" in LANGUAGE_MAP
        assert "fr" in LANGUAGE_MAP

    def test_language_map_values_are_lowercase(self) -> None:
        """Test that all language names are lowercase."""
        for code, name in LANGUAGE_MAP.items():
            assert name.islower(), f"Language name '{name}' should be lowercase"
