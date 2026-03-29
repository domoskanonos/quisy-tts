from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from schemas.requests import ConcatenateAudioRequest
from audio.processor import SoxAudioProcessor
from config import ProjectConfig
from core import CleanupService
from api.dependencies import get_cleanup_service
import os
import uuid

router: APIRouter = APIRouter(tags=["Audio Processing"])
settings = ProjectConfig.get_settings()


@router.post(
    "/upload",
    response_model=dict,
    summary="Upload an audio file",
    description="Uploads a WAV file to the server. Returns the public URL to the uploaded file.",
)
async def upload_audio(
    file: UploadFile = File(..., description="The WAV file to upload"),
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> dict:
    """
    Upload an audio file.

    Example:
        POST /api/audio/upload
        Body: multipart/form-data (file: testaudio.wav)
        Response: {"url": "http://localhost:8045/audio/uploads/uuid.wav"}
    """
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

    # Return URL
    url = f"http://{settings.HOST}:{settings.PORT}/audio/uploads/{filename}"
    return {"url": url}


@router.post(
    "/concatenate",
    response_model=dict,
    summary="Concatenate audio files",
    description="Concatenates multiple existing audio files (uploaded or generated) into a single WAV file. Returns the public URL to the concatenated file.",
)
async def concatenate_audio(
    request: ConcatenateAudioRequest,
) -> dict:
    """
    Concatenate multiple audio files into one.

    Example:
        POST /api/audio/concatenate
        Body: {"audio_files": ["file1.wav", "file2.wav"]}
        Response: {"url": "http://localhost:8045/audio/concat_uuid.wav"}
    """
    output_filename = f"concat_{uuid.uuid4()}.wav"
    output_path = settings.AUDIO_DIR / output_filename
    output_path_str = str(output_path)

    # Prepend output dir to input filenames.
    # Check both AUDIO_DIR and UPLOAD_DIR
    input_paths = []
    for f in request.audio_files:
        p_out = settings.AUDIO_DIR / f
        p_up = settings.UPLOAD_DIR / f

        if p_out.exists():
            input_paths.append(str(p_out))
        elif p_up.exists():
            input_paths.append(str(p_up))
        else:
            raise HTTPException(status_code=404, detail=f"File {f} not found.")

    if not SoxAudioProcessor.concatenate_audio(input_paths, output_path_str):
        raise HTTPException(status_code=500, detail="Concatenation failed.")

    # Return URL
    url = f"http://{settings.HOST}:{settings.PORT}/audio/{output_filename}"
    return {"url": url}
