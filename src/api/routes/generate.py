"""Generation routes for voice management."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from api.dependencies import get_tts_service, get_cleanup_service, get_voice_service
from config import ProjectConfig
from schemas.requests import GenerateRequest
from services import TTSService
from services.voice_service import VoiceService
from core import CleanupService
from schemas import TTSParams
import os

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router: APIRouter = APIRouter(tags=["Generation"])


@router.post("/generate", response_model=None)
async def generate_audio(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    service: TTSService = Depends(get_tts_service),
    cleanup: CleanupService = Depends(get_cleanup_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> FileResponse:
    """Generate audio using base mode (voice cloning) with default model."""
    if voice_service.get_voice(request.voice_id) is None:
        raise HTTPException(status_code=400, detail=f"Voice ID '{request.voice_id}' not found")

    result_path = await service.generate_audio(
        text=request.text,
        language=request.language,
        mode="base",
        model_size=settings.TTS_MODEL_SIZE,
        reference_audio=request.voice_id,
    )
    background_tasks.add_task(cleanup.cleanup_old_files, settings.AUDIO_DIR, 24)
    return FileResponse(
        path=str(result_path),
        media_type="audio/wav",
        filename=result_path.name,
        headers={"Content-Disposition": f"attachment; filename={result_path.name}"},
    )


@router.post("/ssml")
async def generate_ssml(request: Request):
    """Generate audio from SSML."""
    ssml_content = await request.body()
    tts_service = get_tts_service()

    try:
        # Base parameters for the generation. The SSML must include speaker
        # elements with explicit voice IDs. Language is always provided via
        # API calls or SSML speakers; do not hardcode a language here.
        base_params = TTSParams(mode="custom_voice", model_size=settings.TTS_MODEL_SIZE)

        result_path = await tts_service.generate_from_ssml(ssml_content.decode("utf-8"), base_params)

        # Return URL
        filename = os.path.basename(result_path)
        return {"url": f"http://{settings.HOST}:{settings.PORT}/audio/{filename}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
