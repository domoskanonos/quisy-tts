"""Info and utility routes."""

from typing import Any

from fastapi import APIRouter
from config import ProjectConfig
from schemas.languages import LANGUAGE_MAP

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router: APIRouter = APIRouter(tags=["Info"])


@router.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "version": "3.0.0",
        "architecture": "Clean Architecture (Hexagonal)",
        "backend": "qwen-tts",
        "available_endpoints": [
            "/generate/base/0.6b",
            "/generate/base/1.7b",
            "/generate/voice-design/1.7b",
            "/generate/custom-voice/0.6b",
            "/generate/custom-voice/1.7b",
        ],
    }


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.values()))
    return {"languages": languages}
