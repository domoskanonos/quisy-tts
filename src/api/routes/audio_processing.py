from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from schemas.requests import ConcatenateAudioRequest
from audio.processor import SoxAudioProcessor
from config import ProjectConfig
from services import CleanupService
from api.dependencies import get_cleanup_service
import os
import uuid

router: APIRouter = APIRouter(tags=["Audio Processing"])
settings = ProjectConfig.get_settings()


@router.post("/upload", response_model=dict)
async def upload_audio(
    file: UploadFile = File(...),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> dict:
    """Upload an audio file."""
    if not file.filename or not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are allowed.")

    # Limit file size to 20MB
    MAX_SIZE = 20 * 1024 * 1024
    content = await file.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB).")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.wav"
    filepath = settings.UPLOAD_DIR / filename

    with open(filepath, "wb") as buffer:
        buffer.write(content)

    # Cleanup old files
    cleanup.cleanup_old_files(settings.UPLOAD_DIR, 24)

    return {"filename": filename}


@router.post("/concatenate", response_model=None)
async def concatenate_audio(
    request: ConcatenateAudioRequest,
) -> FileResponse:
    """Concatenate multiple audio files into one."""
    output_filename = f"concat_{uuid.uuid4()}.wav"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

    # Prepend output dir to input filenames.
    # Check both OUTPUT_DIR and UPLOAD_DIR
    input_paths = []
    for f in request.audio_files:
        p_out = settings.OUTPUT_DIR / f
        p_up = settings.UPLOAD_DIR / f

        if p_out.exists():
            input_paths.append(str(p_out))
        elif p_up.exists():
            input_paths.append(str(p_up))
        else:
            raise HTTPException(status_code=404, detail=f"File {f} not found.")

    if not SoxAudioProcessor.concatenate_audio(input_paths, output_path):
        raise HTTPException(status_code=500, detail="Concatenation failed.")

    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename=output_filename,
        headers={"Content-Disposition": f"attachment; filename={output_filename}"},
    )
