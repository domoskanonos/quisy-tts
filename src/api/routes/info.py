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
            "/api/generate/generate",
            "/api/generate/ssml",
            "/api/voices/",
            "/api/voices/search",
            "/api/voices/terms",
            "/api/audio",
        ],
    }


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.keys()))
    return {"languages": languages}
