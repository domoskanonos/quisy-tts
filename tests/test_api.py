"""Comprehensive test suite for Cosmo TTS API with restructured endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette import status


# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from project.schemas import (
    LANGUAGE_MAP,
    BaseGenerateRequest,
    CustomVoiceRequest,
    TTSParams,
    VoiceDesignRequest,
    resolve_language,
)


class TestLanguageMapping:
    """Tests for the language code mapping functionality."""

    def test_short_code_to_full_name(self) -> None:
        """Test that short codes are correctly resolved to full names."""
        assert resolve_language("de") == "german"

    def test_english_mapping(self) -> None:
        """Test English language mapping."""
        assert resolve_language("en") == "english"

    def test_full_name_passthrough(self) -> None:
        """Test that full names pass through unchanged."""
        assert resolve_language("german") == "german"

    def test_unknown_code_passthrough(self) -> None:
        """Test that unknown codes pass through unchanged."""
        assert resolve_language("unknown") == "unknown"

    def test_all_supported_languages(self) -> None:
        """Test all supported language mappings."""
        expected = {
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
        for code, full_name in expected.items():
            assert resolve_language(code) == full_name


class TestBaseGenerateRequest:
    """Tests for the BaseGenerateRequest schema."""

    def test_minimal_request(self) -> None:
        """Test creating a request with only required fields."""
        request = BaseGenerateRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.language == "german"
        assert request.reference_audio is None

    def test_full_request(self) -> None:
        """Test creating a request with all fields."""
        request = BaseGenerateRequest(
            text="Test text",
            language="english",
            reference_audio="test.wav",
            ref_text="Test transcript",
        )
        assert request.text == "Test text"
        assert request.language == "english"
        assert request.reference_audio == "test.wav"


class TestVoiceDesignRequest:
    """Tests for the VoiceDesignRequest schema."""

    def test_minimal_request(self) -> None:
        """Test creating a request with required fields."""
        request = VoiceDesignRequest(text="Hello", instruct="a calm narrator")
        assert request.text == "Hello"
        assert request.instruct == "a calm narrator"
        assert request.language == "english"

    def test_custom_language(self) -> None:
        """Test with custom language."""
        request = VoiceDesignRequest(
            text="Hallo", instruct="ein ruhiger Erzähler", language="german"
        )
        assert request.language == "german"


class TestCustomVoiceRequest:
    """Tests for the CustomVoiceRequest schema."""

    def test_minimal_request(self) -> None:
        """Test creating a request with required fields."""
        request = CustomVoiceRequest(text="Hello", speaker="eric")
        assert request.text == "Hello"
        assert request.speaker == "eric"
        assert request.language == "german"

    def test_with_instruct(self) -> None:
        """Test with optional instruct field."""
        request = CustomVoiceRequest(
            text="Hello", speaker="eric", instruct="speak slowly"
        )
        assert request.instruct == "speak slowly"


class TestTTSParams:
    """Tests for the TTSParams model."""

    def test_default_values(self) -> None:
        """Test default TTSParams values."""
        params = TTSParams()
        assert params.language == "german"
        assert params.mode == "base"
        assert params.model_size == "1.7B"

    def test_resolved_language(self) -> None:
        """Test language resolution."""
        params = TTSParams(language="de")
        assert params.resolved_language == "german"


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
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available_endpoints" in data

    def test_openapi_endpoint(self, client: TestClient) -> None:
        """Test the OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "/generate/base/0.6b" in data["paths"]
        assert "/generate/base/1.7b" in data["paths"]
        assert "/generate/voice-design/1.7b" in data["paths"]
        assert "/generate/custom-voice/0.6b" in data["paths"]
        assert "/generate/custom-voice/1.7b" in data["paths"]

    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test the Swagger UI endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_base_endpoint_validation(self, client: TestClient) -> None:
        """Test that missing 'text' field returns validation error."""
        response = client.post("/generate/base/0.6b", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_voice_design_endpoint_validation(self, client: TestClient) -> None:
        """Test that missing required fields returns validation error."""
        response = client.post("/generate/voice-design/1.7b", json={"text": "Hello"})
        # Missing 'instruct' field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_custom_voice_endpoint_validation(self, client: TestClient) -> None:
        """Test that missing 'speaker' field returns validation error."""
        response = client.post("/generate/custom-voice/0.6b", json={"text": "Hello"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLanguageMapConstant:
    """Tests for the LANGUAGE_MAP constant."""

    def test_language_map_has_common_languages(self) -> None:
        """Test that LANGUAGE_MAP contains common languages."""
        assert "de" in LANGUAGE_MAP
        assert "en" in LANGUAGE_MAP
        assert "fr" in LANGUAGE_MAP

    def test_language_map_values_are_lowercase(self) -> None:
        """Test that all language names are lowercase."""
        for name in LANGUAGE_MAP.values():
            assert name.islower()
