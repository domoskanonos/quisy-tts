"""WebSocket route for real-time TTS streaming."""

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from project.api.dependencies import get_tts_service
from project.config import ProjectConfig
from project.services import TTSService


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    service: TTSService = Depends(get_tts_service),
) -> None:
    """WebSocket for real-time TTS.

    Send JSON with: text, language, mode, model_size, speaker, instruct
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            text = payload.get("text")
            if not text:
                continue

            logger.info(f"WebSocket generating: {text[:50]}")

            stream = service.generate_stream(
                text=text,
                language=payload.get("language", "german"),
                mode=payload.get("mode", "base"),
                model_size=payload.get("model_size", settings.DEFAULT_MODEL_SIZE),
                speaker=payload.get("speaker"),
                instruct=payload.get("instruct"),
            )

            for chunk in stream:
                await websocket.send_bytes(chunk)

            await websocket.send_text(json.dumps({"status": "done"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
