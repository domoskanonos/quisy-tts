import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech
from project.schemas import GenerateRequest, TTSParams


app = FastAPI(title="Cosmo TTS API")
logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

# Initialize TTS globally
tts_engine = QwenTextToSpeech()


@app.get("/")
def read_root():
    return {
        "message": "Cosmo TTS API is running",
        "model_size": settings.DEFAULT_MODEL_SIZE,
    }


@app.post("/generate")
async def generate_audio(request: GenerateRequest):
    """Generate audio from text and return the WAV file."""
    try:
        filename = f"{uuid.uuid4()}.wav"
        output_path = Path(settings.OUTPUT_DIR) / filename

        params = TTSParams(
            language_id=request.language_id or settings.DEFAULT_LANGUAGE,
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
            mode=request.mode,
            instruct=request.instruct,
            speaker=request.speaker,
            model_size=request.model_size,
        )

        result_path = tts_engine.generate_and_save(
            request.text, str(output_path), params
        )

        if os.path.exists(result_path):
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
