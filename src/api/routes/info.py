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
    return {"status": "ok", "message": "Cosmo TTS API is running. See /api/docs for documentation.", "version": "3.0.0"}


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.keys()))
    return {"languages": languages}
