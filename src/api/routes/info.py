"""Info and utility routes."""

import contextlib
from importlib.metadata import version as pkg_version
from typing import Any

from fastapi import APIRouter

from config import ProjectConfig
from schemas.languages import LANGUAGE_MAP

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router: APIRouter = APIRouter(tags=["Info"])

APP_VERSION = "0.0.0"
with contextlib.suppress(Exception):
    APP_VERSION = pkg_version("quisy-tts")


@router.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "status": "ok",
        "message": "Quisy TTS API is running. See /api/docs for documentation.",
        "version": APP_VERSION,
    }


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.keys()))
    return {"languages": languages}
