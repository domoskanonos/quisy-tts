"""CRUD routes for voice management."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Path, File
from api.dependencies import get_tts_service, get_voice_service
from config import ProjectConfig
from schemas.voice import VoiceCreate, VoiceListResponse, VoiceResponse
from services import TTSService
from services.voice_service import VoiceService

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


router: APIRouter = APIRouter(tags=["Voice Management"])


# ─── CRUD Operations ─────────────────────────────────────────


@router.get("/", response_model=VoiceListResponse)
def list_voices(voice_service: VoiceService = Depends(get_voice_service)) -> dict[str, Any]:
    """List all registered voices (defaults + custom)."""
    voices = voice_service.list_voices()
    return {"voices": voices, "total": len(voices)}


@router.get("/{voice_id}", response_model=VoiceResponse)
def get_voice(
    voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$"), voice_service: VoiceService = Depends(get_voice_service)
) -> dict:
    """Get a single voice by ID."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    voice = voice_service.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice


@router.post("/", response_model=dict, status_code=200)
async def create_voice(
    data: VoiceCreate,
    service: TTSService = Depends(get_tts_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> dict:
    """Create a new voice entry, generate its reference audio, and return status."""
    # 1. Create DB entry
    voice = voice_service.create_voice(
        name=data.voice_id,
        example_text=data.text,
        instruct=data.instruct,
        language=data.language,
    )
    if voice is None:
        raise HTTPException(status_code=500, detail="Voice creation failed")

    # 2. Generate reference audio (voice_design, 1.7B)
    try:
        result_path = await service.generate_audio(
            text=data.text,
            language=data.language,
            mode="voice_design",
            model_size=settings.TTS_MODEL_SIZE,
            instruct=data.instruct,
        )
        # 3. Associate audio with the new voice
        audio_data = result_path.read_bytes()
        voice_service.set_audio(voice["voice_id"], audio_data, result_path.name)

        # Cleanup temp file
        result_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Failed to generate reference audio for voice {voice['voice_id']}: {e}")
        # Delete voice entry since generation failed?
        voice_service.delete_voice(voice["voice_id"])
        raise HTTPException(status_code=503, detail=f"Voice created but audio generation failed: {e}")

    return {"status": "success", "voice_id": voice["voice_id"]}


@router.delete("/{voice_id}", status_code=204)
def delete_voice(
    voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$"), voice_service: VoiceService = Depends(get_voice_service)
) -> None:
    """Delete a voice and its associated audio file."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")

    # Check if it's a default voice
    voice = voice_service.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")

    deleted = voice_service.delete_voice(voice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")


@router.post("/{voice_id}/audio", response_model=VoiceResponse)
async def upload_audio(
    file: UploadFile = File(...),
    voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$"),
    voice_service: VoiceService = Depends(get_voice_service),
) -> dict:
    """Upload or replace the audio file for a voice."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio files are allowed")

    audio_data = await file.read()

    if len(audio_data) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=400, detail="Audio file too large (max 50 MB)")

    voice = voice_service.set_audio(
        voice_id=voice_id,
        audio_data=audio_data,
        original_filename=file.filename or "upload.wav",
    )
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice
