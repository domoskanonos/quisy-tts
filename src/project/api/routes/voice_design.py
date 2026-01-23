"""Voice design mode routes (1.7B only)."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from project.api.dependencies import get_cleanup_service, get_tts_service
from project.config import ProjectConfig
from project.core import AudioGenerationError, CleanupService
from project.schemas import VoiceDesignRequest
from project.services import TTSService


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["Voice Design Mode"])


@router.post("/1.7b", response_model=None)
async def generate_voice_design_17b(
    request: VoiceDesignRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> FileResponse:
    """Generate audio using voice design mode with 1.7B model."""
    try:
        result_path = await service.generate_audio(
            text=request.text,
            language=request.language,
            mode="voice_design",
            model_size="1.7B",
            instruct=request.instruct,
        )

        background_tasks.add_task(cleanup.cleanup_old_files, settings.OUTPUT_DIR, 24)

        return FileResponse(
            path=str(result_path),
            media_type="audio/wav",
            filename=result_path.name,
            headers={"Content-Disposition": "inline"},
        )

    except AudioGenerationError as e:
        logger.error(f"Voice design generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream/1.7b", response_model=None)
async def stream_voice_design_17b(
    request: VoiceDesignRequest,
    service: TTSService = Depends(get_tts_service),
) -> StreamingResponse:
    """Stream audio using voice design mode with 1.7B model."""
    return StreamingResponse(
        service.generate_stream(
            text=request.text,
            language=request.language,
            mode="voice_design",
            model_size="1.7B",
            instruct=request.instruct,
        ),
        media_type="audio/l16; rate=24000; channels=1",
    )
