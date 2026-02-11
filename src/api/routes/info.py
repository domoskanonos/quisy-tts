"""Info and utility routes."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from api.dependencies import get_cleanup_service
from config import ProjectConfig
from core import CleanupService
from schemas.languages import LANGUAGE_MAP

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["Info"])

# Known Qwen3-TTS CustomVoice speakers (from official documentation)
SUPPORTED_SPEAKERS = [
    "Chelsie",
    "Aidan",
    "Serena",
    "Ethan",
    "Vivian",
    "Lucas",
    "Aria",
    "Oliver",
    "Isabel",
    "Caleb",
    "eric",
]


@router.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "version": "3.0.0",
        "architecture": "Clean Architecture (Hexagonal)",
        "backend": "vLLM",
        "available_endpoints": [
            "/generate/base/0.6b",
            "/generate/base/1.7b",
            "/generate/voice-design/1.7b",
            "/generate/custom-voice/0.6b",
            "/generate/custom-voice/1.7b",
        ],
    }


@router.post("/cleanup", response_model=None)
async def trigger_cleanup(
    background_tasks: BackgroundTasks,
    max_age_hours: int = 24,
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> dict[str, str]:
    """Trigger cleanup of old audio files."""
    background_tasks.add_task(cleanup.cleanup_old_files, settings.OUTPUT_DIR, max_age_hours)
    return {"status": "Cleanup scheduled"}


@router.get("/speakers")
def get_speakers() -> dict[str, Any]:
    """Returns the list of supported speakers for CustomVoice mode."""
    return {"speakers": SUPPORTED_SPEAKERS}


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.values()))
    return {"languages": languages}
