import json
import uuid
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech
from project.schemas import GenerateRequest, TTSParams


app = FastAPI(title="Cosmo TTS API")
logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

# Initialize TTS globally
tts_engine = QwenTextToSpeech()


@app.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "model_size": settings.DEFAULT_MODEL_SIZE,
    }


@app.post("/generate")
async def generate_audio(request: GenerateRequest) -> StreamingResponse | FileResponse:
    """Generate audio from text and return the WAV file or stream chunks."""
    try:
        params = TTSParams(
            language_id=request.language_id or settings.DEFAULT_LANGUAGE,
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
            mode=request.mode or "base",
            instruct=request.instruct,
            speaker=request.speaker,
            model_size=request.model_size or settings.DEFAULT_MODEL_SIZE,
        )

        if request.stream:
            return StreamingResponse(
                tts_engine.generate_audio_stream(request.text, params),
                media_type="audio/l16; rate=24000; channels=1",
            )

        filename = f"{uuid.uuid4()}.wav"
        output_path = settings.OUTPUT_DIR / filename

        result_path = tts_engine.generate_and_save(
            request.text, str(output_path), params
        )

        if result_path and Path(result_path).exists():
            return FileResponse(
                path=result_path, media_type="audio/wav", filename=filename
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio")

    except Exception as e:
        logger.error(f"Error in /generate: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket for real-time TTS."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            # Expecting JSON with text and params
            data = await websocket.receive_text()
            payload = json.loads(data)

            text = payload.get("text")
            if not text:
                continue

            # Extract params from payload or use defaults
            params = TTSParams(
                language_id=payload.get("language_id") or settings.DEFAULT_LANGUAGE,
                mode=payload.get("mode") or "base",
                model_size=payload.get("model_size") or settings.DEFAULT_MODEL_SIZE,
                speaker=payload.get("speaker"),
                instruct=payload.get("instruct"),
            )

            logger.info(f"WebSocket generating: {text[:50]}")

            # Use generate_audio_stream to send chunks over WebSocket
            for chunk in tts_engine.generate_audio_stream(text, params):
                await websocket.send_bytes(chunk)

            # Optionally send an end-of-stream message or just wait for next text
            await websocket.send_text(json.dumps({"status": "done"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


def main() -> None:
    """Start the FastAPI server."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT}"
    )
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    main()
