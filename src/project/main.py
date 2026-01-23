"""Cosmo TTS API - FastAPI application with separate endpoints per model/mode."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse

from project.config import ProjectConfig
from project.qwen_tts_engine import QwenTextToSpeech
from project.schemas import (
    BaseGenerateRequest,
    CustomVoiceRequest,
    TTSParams,
    VoiceDesignRequest,
    resolve_language,
)


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

# Initialize TTS globally
tts_engine = QwenTextToSpeech()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application lifecycle."""
    logger.info("Registered Routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            logger.info(f" -> {methods} {route.path}")
        else:
            logger.info(f" -> {route.path}")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title="Cosmo TTS API",
    description=(
        "Text-to-Speech API powered by Qwen3-TTS. "
        "Supports base (voice cloning), voice design, and custom voice modes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Status Endpoint
# =============================================================================


@app.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "available_endpoints": [
            "/generate/base/0.6b",
            "/generate/base/1.7b",
            "/generate/voice-design/1.7b",
            "/generate/custom-voice/0.6b",
            "/generate/custom-voice/1.7b",
        ],
    }


# =============================================================================
# Base Mode Endpoints (Voice Cloning)
# =============================================================================


@app.post("/generate/base/0.6b", response_model=None)
async def generate_base_06b(request: BaseGenerateRequest) -> FileResponse:
    """Generate audio using base mode (voice cloning) with 0.6B model."""
    return await _generate_base(request, model_size="0.6B")


@app.post("/generate/base/1.7b", response_model=None)
async def generate_base_17b(request: BaseGenerateRequest) -> FileResponse:
    """Generate audio using base mode (voice cloning) with 1.7B model."""
    return await _generate_base(request, model_size="1.7B")


@app.post("/stream/base/0.6b", response_model=None)
async def stream_base_06b(request: BaseGenerateRequest) -> StreamingResponse:
    """Stream audio using base mode (voice cloning) with 0.6B model."""
    return await _stream_base(request, model_size="0.6B")


@app.post("/stream/base/1.7b", response_model=None)
async def stream_base_17b(request: BaseGenerateRequest) -> StreamingResponse:
    """Stream audio using base mode (voice cloning) with 1.7B model."""
    return await _stream_base(request, model_size="1.7B")


async def _generate_base(request: BaseGenerateRequest, model_size: str) -> FileResponse:
    """Internal handler for base mode generation."""
    try:
        params = TTSParams(
            language=resolve_language(request.language),
            reference_audio=request.reference_audio,
            ref_text=request.ref_text,
            mode="base",
            model_size=model_size,
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
        raise HTTPException(status_code=500, detail="Failed to generate audio")

    except Exception as e:
        logger.error(f"Error in base generation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_base(
    request: BaseGenerateRequest, model_size: str
) -> StreamingResponse:
    """Internal handler for base mode streaming."""
    params = TTSParams(
        language=resolve_language(request.language),
        reference_audio=request.reference_audio,
        ref_text=request.ref_text,
        mode="base",
        model_size=model_size,
    )
    return StreamingResponse(
        tts_engine.generate_audio_stream(request.text, params),
        media_type="audio/l16; rate=24000; channels=1",
    )


# =============================================================================
# Voice Design Mode Endpoints (1.7B only)
# =============================================================================


@app.post("/generate/voice-design/1.7b", response_model=None)
async def generate_voice_design_17b(request: VoiceDesignRequest) -> FileResponse:
    """Generate audio using voice design mode with 1.7B model."""
    try:
        params = TTSParams(
            language=resolve_language(request.language),
            instruct=request.instruct,
            mode="voice_design",
            model_size="1.7B",
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
        raise HTTPException(status_code=500, detail="Failed to generate audio")

    except Exception as e:
        logger.error(f"Error in voice design generation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/stream/voice-design/1.7b", response_model=None)
async def stream_voice_design_17b(request: VoiceDesignRequest) -> StreamingResponse:
    """Stream audio using voice design mode with 1.7B model."""
    params = TTSParams(
        language=resolve_language(request.language),
        instruct=request.instruct,
        mode="voice_design",
        model_size="1.7B",
    )
    return StreamingResponse(
        tts_engine.generate_audio_stream(request.text, params),
        media_type="audio/l16; rate=24000; channels=1",
    )


# =============================================================================
# Custom Voice Mode Endpoints
# =============================================================================


@app.post("/generate/custom-voice/0.6b", response_model=None)
async def generate_custom_voice_06b(request: CustomVoiceRequest) -> FileResponse:
    """Generate audio using custom voice mode with 0.6B model."""
    return await _generate_custom_voice(request, model_size="0.6B")


@app.post("/generate/custom-voice/1.7b", response_model=None)
async def generate_custom_voice_17b(request: CustomVoiceRequest) -> FileResponse:
    """Generate audio using custom voice mode with 1.7B model."""
    return await _generate_custom_voice(request, model_size="1.7B")


@app.post("/stream/custom-voice/0.6b", response_model=None)
async def stream_custom_voice_06b(request: CustomVoiceRequest) -> StreamingResponse:
    """Stream audio using custom voice mode with 0.6B model."""
    return await _stream_custom_voice(request, model_size="0.6B")


@app.post("/stream/custom-voice/1.7b", response_model=None)
async def stream_custom_voice_17b(request: CustomVoiceRequest) -> StreamingResponse:
    """Stream audio using custom voice mode with 1.7B model."""
    return await _stream_custom_voice(request, model_size="1.7B")


async def _generate_custom_voice(
    request: CustomVoiceRequest, model_size: str
) -> FileResponse:
    """Internal handler for custom voice generation."""
    try:
        params = TTSParams(
            language=resolve_language(request.language),
            speaker=request.speaker,
            instruct=request.instruct,
            mode="custom_voice",
            model_size=model_size,
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
        raise HTTPException(status_code=500, detail="Failed to generate audio")

    except Exception as e:
        logger.error(f"Error in custom voice generation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _stream_custom_voice(
    request: CustomVoiceRequest, model_size: str
) -> StreamingResponse:
    """Internal handler for custom voice streaming."""
    params = TTSParams(
        language=resolve_language(request.language),
        speaker=request.speaker,
        instruct=request.instruct,
        mode="custom_voice",
        model_size=model_size,
    )
    return StreamingResponse(
        tts_engine.generate_audio_stream(request.text, params),
        media_type="audio/l16; rate=24000; channels=1",
    )


# =============================================================================
# WebSocket Endpoint (Real-time streaming)
# =============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket for real-time TTS. Send JSON with text, language, mode, model_size."""
    import json

    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            text = payload.get("text")
            if not text:
                continue

            params = TTSParams(
                language=resolve_language(payload.get("language", "german")),
                mode=payload.get("mode", "base"),
                model_size=payload.get("model_size", settings.DEFAULT_MODEL_SIZE),
                speaker=payload.get("speaker"),
                instruct=payload.get("instruct"),
            )

            logger.info(f"WebSocket generating: {text[:50]}")

            for chunk in tts_engine.generate_audio_stream(text, params):
                await websocket.send_bytes(chunk)

            await websocket.send_text(json.dumps({"status": "done"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# =============================================================================
# Application Entry Point
# =============================================================================


def main() -> None:
    """Start the FastAPI server."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT}"
    )
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    main()
