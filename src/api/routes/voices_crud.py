"""CRUD routes for voice management."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, Path, Body, File
from fastapi.responses import FileResponse

from api.dependencies import get_tts_service
from config import ProjectConfig
from schemas.voice import VoiceCreate, VoiceListResponse, VoiceResponse, VoiceUpdate
from services import TTSService
from services.voice_service import VoiceService

logger = ProjectConfig.get_logger()

logger = ProjectConfig.get_logger()

router: APIRouter = APIRouter(tags=["Voice Management"])

# Singleton service instance
_voice_service: VoiceService | None = None


def _get_service() -> VoiceService:
    """Lazy init the VoiceService singleton."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


# ─── List Voices ─────────────────────────────────────────────────


@router.get("/", response_model=VoiceListResponse)
def list_voices() -> dict[str, Any]:
    """List all registered voices (defaults + custom)."""
    service = _get_service()
    voices = service.list_voices()
    return {"voices": voices, "total": len(voices)}


# ─── Get Voice ───────────────────────────────────────────────────


@router.get("/{voice_id}", response_model=VoiceResponse)
def get_voice(voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$")) -> dict:
    """Get a single voice by ID."""
    # Protect reserved static subpaths from being interpreted as voice IDs.
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    service = _get_service()
    voice = service.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice


# ─── Create Voice ────────────────────────────────────────────────


@router.post("/", response_model=VoiceResponse, status_code=201)
def create_voice(data: VoiceCreate) -> dict:
    """Create a new voice (metadata only, upload audio separately)."""
    service = _get_service()
    voice = service.create_voice(
        name=data.name,
        example_text=data.example_text,
        instruct=data.instruct,
        language=data.language,
    )
    if voice is None:
        raise HTTPException(status_code=500, detail="Voice creation failed")
    return voice


# ─── Update Voice ────────────────────────────────────────────────


@router.put("/{voice_id}", response_model=VoiceResponse)
def update_voice(data: VoiceUpdate = Body(...), voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$")) -> dict:
    """Update voice metadata."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    service = _get_service()
    voice = service.update_voice(
        voice_id=voice_id,
        name=data.name,
        example_text=data.example_text,
        instruct=data.instruct,
        language=data.language,
    )
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice


# ─── Delete Voice ────────────────────────────────────────────────


@router.delete("/{voice_id}", status_code=204)
def delete_voice(voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$")) -> None:
    """Delete a voice and its associated audio file."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    service = _get_service()

    # Check if it's a default voice
    voice = service.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    if voice.get("is_default"):
        raise HTTPException(status_code=403, detail="Default voices cannot be deleted")

    deleted = service.delete_voice(voice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")


# ─── Upload Audio ────────────────────────────────────────────────


@router.post("/{voice_id}/audio", response_model=VoiceResponse)
async def upload_audio(file: UploadFile = File(...), voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$")) -> dict:
    """Upload or replace the audio file for a voice."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio files are allowed")

    service = _get_service()
    audio_data = await file.read()

    if len(audio_data) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(status_code=400, detail="Audio file too large (max 50 MB)")

    voice = service.set_audio(
        voice_id=voice_id,
        audio_data=audio_data,
        original_filename=file.filename or "upload.wav",
    )
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice


# ─── Get Audio ───────────────────────────────────────────────────


@router.get("/{voice_id}/audio", response_model=None)
def get_audio(voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$")) -> FileResponse:
    """Stream the audio file for a voice."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail="Audio not found for this voice")
    service = _get_service()
    audio_path = service.get_audio_path(voice_id)
    if audio_path is None:
        raise HTTPException(status_code=404, detail="Audio not found for this voice")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@router.get("/{voice_id}/ensure-audio/status", response_model=dict)
def ensure_audio_status(
    voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$"), tts_service: TTSService = Depends(get_tts_service)
) -> dict:
    """Return background generation status for a voice."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    status = tts_service.get_reference_generation_status(voice_id)
    return status


# ─── Ensure Audio (Background Generation) ────────────────────────


async def _generate_preview_task(
    voice_id: str,
    text: str,
    language: str,
    instruct: str | None,
    tts_service: TTSService,
) -> None:
    """Background task to generate preview audio."""
    try:
        logger.info(f"Starting background preview generation for voice {voice_id}...")

        # Determine mode based on available data
        # If we have an instruct, use voice_design (1.7B)
        # If not, we might fail or default to something else?
        # But `ensure_audio` is usually for voices that HAVE metadata but NO audio.
        # Ideally we use voice_design since it's the only way to generate FROM metadata.

        mode = "voice_design"
        final_instruct = instruct or "A clear and natural voice."

        # Generate
        path = await tts_service.generate_audio(
            text=text,
            language=language,
            mode=mode,
            model_size="1.7B",  # VoiceDesign is 1.7B only
            instruct=final_instruct,
        )

        if path and path.exists():
            # Save to voice service (database + persistent storage)
            service = _get_service()
            audio_data = path.read_bytes()
            service.set_audio(voice_id, audio_data, f"preview_{voice_id}.wav")

            # Cleanup temp file from output dir if needed, or let cleanup service handle it
            try:
                path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp preview file: {e}")

            logger.info(f"Background generation completed for voice {voice_id}")

    except Exception as e:
        logger.error(f"Background generation failed for voice {voice_id}: {e}")


@router.post("/{voice_id}/ensure-audio", status_code=202)
async def ensure_audio(
    background_tasks: BackgroundTasks,
    voice_id: str = Path(..., pattern=r"^[a-z0-9_-]+$"),
    force: bool = False,
    tts_service: TTSService = Depends(get_tts_service),
) -> dict[str, str]:
    """Trigger background audio generation if missing."""
    if voice_id in {"terms", "search"}:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    service = _get_service()
    voice = service.get_voice(voice_id)

    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    # If audio already exists and caller did not request a forced regeneration,
    # return early to avoid unnecessary work. If `force` is True we proceed
    # to trigger a regeneration even when an audio file is present.
    if voice.get("audio_filename") and not force:
        return {"status": "exists", "message": "Audio already exists"}

    # Check requirements: we only auto-generate when an instruct is available
    if not voice.get("instruct"):
        raise HTTPException(
            status_code=400, detail="Voice has no instruct text; automatic generation is disabled for this voice"
        )

    # Trigger background generation via TTS service (idempotent)
    tts_service.trigger_reference_audio_generation(voice_id, force=force)
    return {"status": "triggered", "message": "Generation started in background"}
