"""Simple WebSocket status manager for broadcasting reference-generation events.

This module exposes a singleton `status_ws_manager` that other parts of the
application can import and use to broadcast JSON events to connected clients.

Clients connect to the `/ws/status` endpoint and send subscribe/unsubscribe
commands to receive events for specific `voice_id`s or for all voices.
"""

import asyncio
import json
from typing import Dict, Set

from fastapi import WebSocket


class WebSocketStatusManager:
    def __init__(self) -> None:
        # voice_id -> set of WebSocket
        self._voice_subscribers: Dict[str, Set[WebSocket]] = {}
        # websockets that subscribed to all voices
        self._all_subscribers: Set[WebSocket] = set()
        # reverse map for cleanup: websocket -> set of voice_ids
        self._ws_to_voices: Dict[WebSocket, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._ws_to_voices.setdefault(websocket, set())

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            # remove from all subscribers
            self._all_subscribers.discard(websocket)
            # remove from voice-specific lists
            voices = self._ws_to_voices.pop(websocket, set())
            for v in voices:
                subs = self._voice_subscribers.get(v)
                if subs:
                    subs.discard(websocket)
                    if not subs:
                        self._voice_subscribers.pop(v, None)

    async def subscribe(self, websocket: WebSocket, voice_id: str | None) -> None:
        """Subscribe websocket to a voice_id. If voice_id is None, subscribe to all."""
        async with self._lock:
            if voice_id is None:
                self._all_subscribers.add(websocket)
                # also mark in reverse map as wildcard with empty string key
                self._ws_to_voices.setdefault(websocket, set()).add("__ALL__")
            else:
                subs = self._voice_subscribers.setdefault(voice_id, set())
                subs.add(websocket)
                self._ws_to_voices.setdefault(websocket, set()).add(voice_id)

    async def unsubscribe(self, websocket: WebSocket, voice_id: str | None) -> None:
        async with self._lock:
            if voice_id is None:
                self._all_subscribers.discard(websocket)
                s = self._ws_to_voices.get(websocket)
                if s:
                    s.discard("__ALL__")
            else:
                subs = self._voice_subscribers.get(voice_id)
                if subs:
                    subs.discard(websocket)
                s = self._ws_to_voices.get(websocket)
                if s:
                    s.discard(voice_id)

    async def _safe_send(self, websocket: WebSocket, message: str) -> None:
        try:
            await websocket.send_text(message)
        except Exception:
            # best-effort: ignore send errors; disconnect cleaning happens elsewhere
            pass

    async def broadcast(self, event: dict) -> None:
        """Broadcast event to all connected subscribers (including those subscribed to all)."""
        payload = json.dumps(event)
        async with self._lock:
            recipients = set(self._all_subscribers)
            # include all voice-specific subscribers
            for subs in self._voice_subscribers.values():
                recipients.update(subs)
        # send without holding lock to avoid deadlocks
        await asyncio.gather(*(self._safe_send(ws, payload) for ws in recipients), return_exceptions=True)

    async def broadcast_to_voice(self, voice_id: str, event: dict) -> None:
        """Broadcast event for a specific voice_id to subscribers and wildcard subscribers."""
        payload = json.dumps(event)
        async with self._lock:
            recipients = set(self._all_subscribers)
            recipients.update(self._voice_subscribers.get(voice_id, set()))
        await asyncio.gather(*(self._safe_send(ws, payload) for ws in recipients), return_exceptions=True)


# Singleton instance to import from other modules
status_ws_manager = WebSocketStatusManager()
