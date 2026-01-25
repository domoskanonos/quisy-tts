"""Info and utility routes."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from project.api.dependencies import get_cleanup_service
from project.config import ProjectConfig
from project.core import CleanupService
from project.models.manager import ModelManager


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["Info"])


@router.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "version": "3.0.0",
        "architecture": "Clean Architecture (Hexagonal)",
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
    background_tasks.add_task(
        cleanup.cleanup_old_files, settings.OUTPUT_DIR, max_age_hours
    )
    return {"status": "Cleanup scheduled"}


@router.get("/speakers")
def get_speakers() -> dict[str, Any]:
    """Returns the list of supported speakers for CustomVoice mode."""
    try:
        model = ModelManager.get_model(mode="custom_voice", size="1.7B")
        speakers = model.get_supported_speakers()
        return {"speakers": speakers}
    except Exception as e:
        logger.error(f"Failed to get speakers: {e}")
        return {"speakers": [], "error": str(e)}


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    try:
        model = ModelManager.get_model(mode="custom_voice", size="1.7B")
        languages = model.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        logger.error(f"Failed to get languages: {e}")
        return {"languages": [], "error": str(e)}
