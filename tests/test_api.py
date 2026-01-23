"""Comprehensive test suite for Cosmo TTS API v3.0 (Clean Architecture)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette import status


# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from project.core import CacheService, CleanupService, TTSEngine
from project.engine import QwenTextToSpeech
from project.schemas import (
    LANGUAGE_MAP,
    BaseGenerateRequest,
    CustomVoiceRequest,
    VoiceDesignRequest,
    resolve_language,
)
from project.services import FileCacheService, FileCleanupService


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


class TestRequestSchemas:
    """Tests for request schemas."""

    def test_base_request_minimal(self) -> None:
        """Test BaseGenerateRequest with minimal fields."""
        request = BaseGenerateRequest(text="Hello world")
        assert request.text == "Hello world"
        assert request.language == "german"

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
        from project.api import app

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

    def test_base_endpoint_validation(self, client: TestClient) -> None:
        """Test missing 'text' returns validation error."""
        response = client.post("/generate/base/0.6b", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_voice_design_requires_instruct(self, client: TestClient) -> None:
        """Test voice design requires instruct field."""
        response = client.post("/generate/voice-design/1.7b", json={"text": "Hi"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_custom_voice_requires_speaker(self, client: TestClient) -> None:
        """Test custom voice requires speaker field."""
        response = client.post("/generate/custom-voice/0.6b", json={"text": "Hi"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_cleanup_endpoint(self, client: TestClient) -> None:
        """Test cleanup endpoint."""
        response = client.post("/cleanup")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "Cleanup scheduled"


class TestLanguageMapConstant:
    """Tests for LANGUAGE_MAP constant."""

    def test_has_common_languages(self) -> None:
        """Test LANGUAGE_MAP has common languages."""
        assert "de" in LANGUAGE_MAP
        assert "en" in LANGUAGE_MAP

    def test_values_are_lowercase(self) -> None:
        """Test all values are lowercase."""
        for name in LANGUAGE_MAP.values():
            assert name.islower()
