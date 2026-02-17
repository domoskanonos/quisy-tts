"""CRUD routes for voice management."""

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from config import ProjectConfig
from schemas.voice import VoiceCreate, VoiceListResponse, VoiceResponse, VoiceUpdate
from services.voice_service import VoiceService

logger = ProjectConfig.get_logger()

router = APIRouter(tags=["Voice Management"])

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
    """List all registered custom voices."""
    service = _get_service()
    voices = service.list_voices()
    return {"voices": voices, "total": len(voices)}


# ─── Get Voice ───────────────────────────────────────────────────


@router.get("/{voice_id}", response_model=VoiceResponse)
def get_voice(voice_id: str) -> dict:
    """Get a single voice by ID."""
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
    voice = service.create_voice(name=data.name, example_text=data.example_text)
    return voice


# ─── Update Voice ────────────────────────────────────────────────


@router.put("/{voice_id}", response_model=VoiceResponse)
def update_voice(voice_id: str, data: VoiceUpdate) -> dict:
    """Update voice metadata."""
    service = _get_service()
    voice = service.update_voice(
        voice_id=voice_id,
        name=data.name,
        example_text=data.example_text,
    )
    if voice is None:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")
    return voice


# ─── Delete Voice ────────────────────────────────────────────────


@router.delete("/{voice_id}", status_code=204)
def delete_voice(voice_id: str) -> None:
    """Delete a voice and its associated audio file."""
    service = _get_service()
    deleted = service.delete_voice(voice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Voice {voice_id} not found")


# ─── Upload Audio ────────────────────────────────────────────────


@router.post("/{voice_id}/audio", response_model=VoiceResponse)
async def upload_audio(voice_id: str, file: UploadFile) -> dict:
    """Upload or replace the audio file for a voice."""
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
def get_audio(voice_id: str) -> FileResponse:
    """Stream the audio file for a voice."""
    service = _get_service()
    audio_path = service.get_audio_path(voice_id)
    if audio_path is None:
        raise HTTPException(status_code=404, detail="Audio not found for this voice")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=audio_path.name,
    )
