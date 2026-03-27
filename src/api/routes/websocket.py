"""WebSocket route for real-time TTS streaming."""

import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.dependencies import get_tts_service
from config import ProjectConfig
from services import TTSService


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{model_size}")
async def websocket_endpoint(
    websocket: WebSocket,
    model_size: str,
    service: TTSService = Depends(get_tts_service),
) -> None:
    """WebSocket for real-time TTS.

    Send JSON with: text, language, mode, speaker, instruct
    """
    await websocket.accept()

    # Normalize model size
    model_size = model_size.upper()
    if model_size not in ["0.6B", "1.7B"]:
        await websocket.close(code=1003, reason="Invalid model size")
        return

    logger.info(f"WebSocket connection established for {model_size}")

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
                model_size=model_size,
                speaker=payload.get("speaker"),
                instruct=payload.get("instruct"),
            )

            async for chunk in stream:
                await websocket.send_bytes(chunk)

            await websocket.send_text(json.dumps({"status": "done"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    """WebSocket endpoint for broadcasting reference-generation status events.

    Client may send JSON commands to control subscriptions:
      - {"action": "subscribe", "voice_id": "<id>"}  -> subscribe to that voice
      - {"action": "subscribe", "voice_id": null}    -> subscribe to all voices
      - {"action": "unsubscribe", "voice_id": "<id>"}
    """
    from api.websocket_status_manager import status_ws_manager

    await status_ws_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except Exception:
                # Ignore invalid JSON
                continue

            action = payload.get("action")
            voice_id = payload.get("voice_id") if "voice_id" in payload else None
            if action == "subscribe":
                await status_ws_manager.subscribe(websocket, voice_id)
            elif action == "unsubscribe":
                await status_ws_manager.unsubscribe(websocket, voice_id)
            else:
                # Unknown action: ignore
                continue

    except WebSocketDisconnect:
        await status_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Status WS error: {e}")
        await status_ws_manager.disconnect(websocket)
        await websocket.close()
