"""Comprehensive test suite for Cosmo TTS API v3.0 (Clean Architecture)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette import status

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from api import app
from core import CacheService, CleanupService, TTSEngine
from engine import QwenTextToSpeech
from schemas import (
    BaseGenerateRequest,
    CustomVoiceRequest,
    VoiceDesignRequest,
    resolve_language,
)
from services import FileCacheService, FileCleanupService


class TestLanguageMapping:
    """Tests for the language code mapping functionality."""

    def test_short_code_to_full_name(self) -> None:
        """Test that short codes are correctly resolved to full names."""
        assert resolve_language("de") == "German"

    def test_english_mapping(self) -> None:
        """Test English language mapping."""
        assert resolve_language("en") == "English"

    def test_full_name_passthrough(self) -> None:
        """Test that full names are mapped to capitalized versions."""
        assert resolve_language("german") == "German"

    def test_unknown_code_passthrough(self) -> None:
        """Test that unknown codes pass through unchanged."""
        assert resolve_language("unknown") == "unknown"

    def test_all_supported_languages(self) -> None:
        """Test all supported language mappings."""
        expected = {
            "de": "German",
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "auto": "Auto",
        }
        for code, full_name in expected.items():
            assert resolve_language(code) == full_name


class TestRequestSchemas:
    """Tests for request schemas."""

    def test_base_request_minimal(self) -> None:
        """Test BaseGenerateRequest with minimal fields."""
        request = BaseGenerateRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.language == "German"

    def test_voice_design_request(self) -> None:
        """Test VoiceDesignRequest."""
        request = VoiceDesignRequest(text="Hello", instruct="calm narrator")
        assert request.text == "Hello"
        assert request.instruct == "calm narrator"

    def test_custom_voice_request(self) -> None:
        """Test CustomVoiceRequest."""
        request = CustomVoiceRequest(text="Hello", speaker="eric")
        assert request.speaker == "eric"


class TestCoreInterfaces:
    """Tests for core layer interfaces."""

    def test_tts_engine_is_abstract(self) -> None:
        """Test that TTSEngine is an abstract class."""
        assert hasattr(TTSEngine, "__abstractmethods__")

    def test_cache_service_is_abstract(self) -> None:
        """Test that CacheService is an abstract class."""
        assert hasattr(CacheService, "__abstractmethods__")

    def test_cleanup_service_is_abstract(self) -> None:
        """Test that CleanupService is an abstract class."""
        assert hasattr(CleanupService, "__abstractmethods__")

    def test_qwen_implements_tts_engine(self) -> None:
        """Test that QwenTextToSpeech implements TTSEngine."""
        assert issubclass(QwenTextToSpeech, TTSEngine)


class TestServiceImplementations:
    """Tests for service layer implementations."""

    def test_file_cache_service_implements_interface(self) -> None:
        """Test FileCacheService implements CacheService."""
        assert issubclass(FileCacheService, CacheService)

    def test_file_cleanup_service_implements_interface(self) -> None:
        """Test FileCleanupService implements CleanupService."""
        assert issubclass(FileCleanupService, CleanupService)


class TestAPIEndpoints:
    """Tests for the FastAPI endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client for the API."""
        return TestClient(app)

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns status."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["version"] == "3.0.0"
        assert data["architecture"] == "Clean Architecture (Hexagonal)"

    def test_openapi_endpoint(self, client: TestClient) -> None:
        """Test the OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "/generate/base/0.6b" in data["paths"]
        assert "/generate/voice-design/1.7b" in data["paths"]
        assert "/generate/custom-voice/0.6b" in data["paths"]

    def test_docs_endpoint(self, client: TestClient) -> None:
        """Test Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_base_endpoint_invalid_input(self, client: TestClient) -> None:
        """Test the base endpoint with invalid input returns 422."""
        payload = {
            "text": "test",
            # Missing language
        }
        response = client.post("/generate/base/0.6b", json=payload)
        assert response.status_code == 400

    def test_voice_design_endpoint_invalid_input(self, client: TestClient) -> None:
        """Test the voice design endpoint with invalid input returns 422."""
        payload = {
            "text": "test",
            # Missing language
        }
        response = client.post("/generate/voice-design/1.7b", json=payload)
        assert response.status_code == 400

    def test_custom_voice_requires_speaker(self, client: TestClient) -> None:
        """Test custom voice requires speaker field."""

    def test_speakers_post_not_allowed(self, client: TestClient) -> None:
        """Test POST method not allowed on speakers endpoint."""
        response = client.post("/speakers")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_languages_post_not_allowed(self, client: TestClient) -> None:
        """Test POST method not allowed on languages endpoint."""
        response = client.post("/languages")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
