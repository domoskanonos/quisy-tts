"""Base mode (voice cloning) routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from api.dependencies import get_cleanup_service, get_tts_service, get_voice_service
from config import ProjectConfig
from core import (
    AudioGenerationError,
    CleanupService,
    InvalidLanguageError,
    ReferenceAudioNotFoundError,
)
from schemas import BaseGenerateRequest
from services import TTSService
from services.voice_service import VoiceService

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["Base Mode (Voice Cloning)"])


@router.post("/0.6b", response_model=None)
async def generate_base_06b(
    request: BaseGenerateRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> FileResponse:
    """Generate audio using base mode (voice cloning) with 0.6B model."""
    # If a reference_audio is supplied it must be a voice ID (filenames are no longer accepted)
    if request.reference_audio:
        if voice_service.get_voice(request.reference_audio) is None:
            raise HTTPException(status_code=400, detail=f"Reference voice id '{request.reference_audio}' not found")
    return await _generate(request, "0.6B", service, background_tasks, cleanup)


@router.post("/1.7b", response_model=None)
async def generate_base_17b(
    request: BaseGenerateRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> FileResponse:
    """Generate audio using base mode (voice cloning) with 1.7B model."""
    if request.reference_audio:
        if voice_service.get_voice(request.reference_audio) is None:
            raise HTTPException(status_code=400, detail=f"Reference voice id '{request.reference_audio}' not found")
    return await _generate(request, "1.7B", service, background_tasks, cleanup)


async def _generate(
    request: BaseGenerateRequest,
    model_size: str,
    service: TTSService,
    background_tasks: BackgroundTasks,
    cleanup: CleanupService,
) -> FileResponse:
    """Internal handler for base mode generation."""
    try:
        result_path = await service.generate_audio(
            text=request.text,
            language=request.language,
            mode="base",
            model_size=model_size,
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
        )

        background_tasks.add_task(cleanup.cleanup_old_files, settings.OUTPUT_DIR, 24)

        return FileResponse(
            path=str(result_path),
            media_type="audio/wav",
            filename=result_path.name,
            headers={"Content-Disposition": f"attachment; filename={result_path.name}"},
        )

    except (ReferenceAudioNotFoundError, InvalidLanguageError) as e:
        logger.warning(f"Invalid base generation request: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except AudioGenerationError as e:
        logger.error(f"Base generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream/0.6b", response_model=None)
async def stream_base_06b(
    request: BaseGenerateRequest,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> StreamingResponse:
    """Stream audio using base mode (voice cloning) with 0.6B model."""
    if request.reference_audio:
        if voice_service.get_voice(request.reference_audio) is None:
            raise HTTPException(status_code=400, detail=f"Reference voice id '{request.reference_audio}' not found")
    return _stream(request, "0.6B", service)


@router.post("/stream/1.7b", response_model=None)
async def stream_base_17b(
    request: BaseGenerateRequest,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> StreamingResponse:
    """Stream audio using base mode (voice cloning) with 1.7B model."""
    if request.reference_audio:
        if voice_service.get_voice(request.reference_audio) is None:
            raise HTTPException(status_code=400, detail=f"Reference voice id '{request.reference_audio}' not found")
    return _stream(request, "1.7B", service)


def _stream(
    request: BaseGenerateRequest,
    model_size: str,
    service: TTSService,
) -> StreamingResponse:
    """Internal handler for base mode streaming."""
    return StreamingResponse(
        service.generate_stream(
            text=request.text,
            language=request.language,
            mode="base",
            model_size=model_size,
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
        ),
        media_type="audio/l16; rate=24000; channels=1",
    )
