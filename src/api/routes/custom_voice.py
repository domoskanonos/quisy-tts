"""Custom voice mode routes."""

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
from schemas import CustomVoiceRequest
from services import TTSService, VoiceService

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router: APIRouter = APIRouter(tags=["Custom Voice Mode"])


@router.post("/0.6b", response_model=None)
async def generate_custom_voice_06b(
    request: CustomVoiceRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> FileResponse:
    """Generate audio using custom voice mode with 0.6B model."""
    return await _generate(request, "0.6B", service, voice_service, background_tasks, cleanup)


@router.post("/1.7b", response_model=None)
async def generate_custom_voice_17b(
    request: CustomVoiceRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> FileResponse:
    """Generate audio using custom voice mode with 1.7B model."""
    return await _generate(request, "1.7B", service, voice_service, background_tasks, cleanup)


async def _generate(
    request: CustomVoiceRequest,
    model_size: str,
    service: TTSService,
    voice_service: VoiceService,
    background_tasks: BackgroundTasks,
    cleanup: CleanupService,
) -> FileResponse:
    """Internal handler for custom voice generation."""
    try:
        # Resolve speaker from DB and require a voice ID
        voice = voice_service.get_voice_by_name(request.speaker)
        if not voice:
            raise ReferenceAudioNotFoundError(f"Speaker '{request.speaker}' not found in database.")

        # Only accept voice IDs now: pass the voice id into the engine.
        speaker_id = voice["id"]
        reference_audio = None

        result_path = await service.generate_audio(
            text=request.text,
            language=request.language,
            mode="custom_voice",
            model_size=model_size,
            speaker=speaker_id,
            reference_audio=reference_audio,
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
    voice_service: VoiceService = Depends(get_voice_service),
) -> StreamingResponse:
    """Stream audio using custom voice mode with 0.6B model."""
    return _stream(request, "0.6B", service, voice_service)


@router.post("/stream/1.7b", response_model=None)
async def stream_custom_voice_17b(
    request: CustomVoiceRequest,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> StreamingResponse:
    """Stream audio using custom voice mode with 1.7B model."""
    return _stream(request, "1.7B", service, voice_service)


def _stream(
    request: CustomVoiceRequest,
    model_size: str,
    service: TTSService,
    voice_service: VoiceService,
) -> StreamingResponse:
    """Internal handler for custom voice streaming.

    Note: the API now requires a speaker that exists in the DB; only voice IDs
    (via their names in the request) are accepted — filenames are not allowed.
    """

    # Resolve speaker from DB and require voice id
    voice = voice_service.get_voice_by_name(request.speaker)
    if not voice:
        raise ReferenceAudioNotFoundError(f"Speaker '{request.speaker}' not found in database.")

    speaker_id = voice["id"]
    reference_audio = None

    return StreamingResponse(
        service.generate_stream(
            text=request.text,
            language=request.language,
            mode="custom_voice",
            model_size=model_size,
            speaker=speaker_id,
            reference_audio=reference_audio,
            instruct=request.instruct,
        ),
        media_type="audio/l16; rate=24000; channels=1",
    )
