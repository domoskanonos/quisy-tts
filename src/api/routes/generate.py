"""Generation routes for voice management."""

from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from api.dependencies import get_tts_service, get_cleanup_service, get_voice_service
from config import ProjectConfig
from schemas.requests import GenerateRequest, GenerateSSMLResponse
from services import TTSService
from services.voice_service import VoiceService
from core import CleanupService
from schemas import TTSParams

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router: APIRouter = APIRouter(tags=["Generation"])


@router.post(
    "/generate",
    response_model=None,
    summary="Standard Text-to-Speech",
    description=(
        "Generates audio from text using a specified voice. "
        "The style instructions (instruct) are automatically retrieved from the database "
        "based on the `voice_id`. This is the recommended endpoint for simple, high-quality narration."
    ),
)
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

    # Ensure reference audio exists before generation
    await service.voice_audio_integrity.ensure_audio(request.voice_id, service.generate_audio)

    voice = voice_service.get_voice(request.voice_id)
    # We already checked for None above, but for type safety:
    instruct = voice.get("instruct") if voice else None

    result_path = await service.generate_audio(
        text=request.text,
        language=request.language,
        mode="base",
        model_size=settings.DEFAULT_MODEL_SIZE,
        reference_audio=request.voice_id,
        instruct=instruct,
    )
    background_tasks.add_task(cleanup.cleanup_old_files, settings.AUDIO_DIR, 24)
    return FileResponse(
        path=str(result_path),
        media_type="audio/wav",
        filename=result_path.name,
        headers={"Content-Disposition": f"attachment; filename={result_path.name}"},
    )


@router.post(
    "/ssml",
    response_model=GenerateSSMLResponse,
    summary="SSML Audio Generation",
    description=(
        "Converts SSML (Speech Synthesis Markup Language) to audio. "
        "Allows for multi-speaker dialogs, custom pauses using `<break>`, "
        "and granular control over the speech output. The root element must be `<speak>`."
    ),
)
async def generate_ssml(
    ssml: str = Body(
        ...,
        description="The SSML content to generate audio from.",
        examples=[
            '<speak><speaker name="german_audiobook_female_narrator_01">Hallo, dies ist ein Test mit SSML.</speaker></speak>'
        ],
    ),
    service: TTSService = Depends(get_tts_service),
) -> GenerateSSMLResponse:
    """Generate audio from SSML."""
    try:
        # Base parameters for the generation
        base_params = TTSParams(mode="custom_voice", model_size=settings.DEFAULT_MODEL_SIZE)

        # Generate audio (WAV and MP3)
        wav_path, mp3_path = await service.generate_from_ssml(ssml, base_params)

        # Return URLs
        def get_audio_url(file_path: Path) -> str:
            filename = file_path.name
            return f"http://{settings.HOST}:{settings.PORT}/audio/{filename}"

        return GenerateSSMLResponse(
            wav_url=get_audio_url(wav_path),
            mp3_url=get_audio_url(mp3_path),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in SSML generation")
        raise HTTPException(status_code=500, detail=str(e))
