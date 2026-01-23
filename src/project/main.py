import os
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech, TTSParams


app = FastAPI(title="Cosmo TTS API")
logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

# Initialize TTS globally
tts_engine = QwenTextToSpeech()


class GenerateRequest(BaseModel):
    text: str
    language_id: str | None = "de"
    reference_audio: str | None = None
    ref_text: str | None = None


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing TTS Engine...")
    tts_engine.initialize()


@app.get("/")
def read_root():
    return {"message": "Cosmo TTS API is running", "model": settings.MODEL_NAME}


@app.post("/generate")
async def generate_audio(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate audio from text and return the WAV file."""
    try:
        filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(settings.OUTPUT_DIR, filename)

        params = TTSParams(
            language_id=request.language_id or settings.DEFAULT_LANGUAGE,
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
        )

        result_path = tts_engine.generate_and_save(request.text, output_path, params)

        if result_path and os.path.exists(result_path):
            # Schedule file deletion after some time if needed,
            # or just return it. For now, we return it.
            return FileResponse(
                path=result_path, media_type="audio/wav", filename=filename
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

    except Exception as e:
        logger.error(f"Error in /generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main() -> None:
    """Start the FastAPI server."""
    import uvicorn

    logger.info(f"Starting {settings.PROJECT_NAME} on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
