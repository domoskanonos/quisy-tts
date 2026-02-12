"""Custom voice mode routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from api.dependencies import get_cleanup_service, get_tts_service
from config import ProjectConfig
from core import (
    AudioGenerationError,
    CleanupService,
    InvalidLanguageError,
    ReferenceAudioNotFoundError,
)
from schemas import CustomVoiceRequest
from services import TTSService

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["Custom Voice Mode"])


@router.post("/0.6b", response_model=None)
async def generate_custom_voice_06b(
    request: CustomVoiceRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> FileResponse:
    """Generate audio using custom voice mode with 0.6B model."""
    return await _generate(request, "0.6B", service, background_tasks, cleanup)


@router.post("/1.7b", response_model=None)
async def generate_custom_voice_17b(
    request: CustomVoiceRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> FileResponse:
    """Generate audio using custom voice mode with 1.7B model."""
    return await _generate(request, "1.7B", service, background_tasks, cleanup)


async def _generate(
    request: CustomVoiceRequest,
    model_size: str,
    service: TTSService,
    background_tasks: BackgroundTasks,
    cleanup: CleanupService,
) -> FileResponse:
    """Internal handler for custom voice generation."""
    try:
        result_path = await service.generate_audio(
            text=request.text,
            language=request.language,
            mode="custom_voice",
            model_size=model_size,
            speaker=request.speaker,
            instruct=request.instruct,
        )

        background_tasks.add_task(cleanup.cleanup_old_files, settings.OUTPUT_DIR, 24)

        return FileResponse(
            path=str(result_path),
            media_type="audio/wav",
            filename=result_path.name,
            headers={"Content-Disposition": f"attachment; filename={result_path.name}"},
        )

    except (ReferenceAudioNotFoundError, InvalidLanguageError) as e:
        logger.warning(f"Invalid custom voice request: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except AudioGenerationError as e:
        logger.error(f"Custom voice generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream/0.6b", response_model=None)
async def stream_custom_voice_06b(
    request: CustomVoiceRequest,
    service: TTSService = Depends(get_tts_service),
) -> StreamingResponse:
    """Stream audio using custom voice mode with 0.6B model."""
    return _stream(request, "0.6B", service)


@router.post("/stream/1.7b", response_model=None)
async def stream_custom_voice_17b(
    request: CustomVoiceRequest,
    service: TTSService = Depends(get_tts_service),
) -> StreamingResponse:
    """Stream audio using custom voice mode with 1.7B model."""
    return _stream(request, "1.7B", service)


def _stream(
    request: CustomVoiceRequest,
    model_size: str,
    service: TTSService,
) -> StreamingResponse:
    """Internal handler for custom voice streaming."""
    return StreamingResponse(
        service.generate_stream(
            text=request.text,
            language=request.language,
            mode="custom_voice",
            model_size=model_size,
            speaker=request.speaker,
            instruct=request.instruct,
        ),
        media_type="audio/l16; rate=24000; channels=1",
    )
