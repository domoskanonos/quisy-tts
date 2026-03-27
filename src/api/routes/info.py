"""Info and utility routes."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from api.dependencies import get_cleanup_service, get_voice_service
from config import ProjectConfig
from core import CleanupService
from schemas.languages import LANGUAGE_MAP
from services import VoiceService

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
def get_speakers(
    voice_service: VoiceService = Depends(get_voice_service),
) -> dict[str, Any]:
    """Returns the list of supported speakers (from DB) for CustomVoice mode."""
    # Return names of all voices in DB that have an audio file or are default
    # Actually, we just return all names, and let the backend handle resolution.
    # Default voices always work (they have instructs or audio).
    # Custom voices need audio for cloning.
    voices = voice_service.list_voices()
    speaker_names = [v["name"] for v in voices]
    return {"speakers": speaker_names}


@router.get("/languages")
def get_languages() -> dict[str, Any]:
    """Returns the list of supported languages."""
    languages = sorted(set(LANGUAGE_MAP.values()))
    return {"languages": languages}
