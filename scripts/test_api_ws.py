import asyncio
import json
import sys
from pathlib import Path

import websockets


# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from project.config import ProjectConfig


settings = ProjectConfig.get_settings()
host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
ENDPOINT = f"ws://{host}:{settings.PORT}/ws"
OUTPUT_DIR = settings.OUTPUT_DIR


async def test_ws() -> None:
    """Tests WebSocket real-time TTS."""
    payload = {
        "text": "Dies ist ein Echtzeit-Test über Web-Sockets. "
        "Die Daten fließen direkt.",
        "language_id": "de",
        "model_size": "0.6B",
    }

    print(f"Connecting to {ENDPOINT}...")
    try:
        async with websockets.connect(ENDPOINT) as websocket:
            print("Sending request...")
            await websocket.send(json.dumps(payload))

            save_path = OUTPUT_DIR / "test_ws_output.raw"
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            chunk_count = 0
            with save_path.open("wb") as f:
                while True:
                    message = await websocket.recv()

                    if isinstance(message, bytes):
                        f.write(message)
                        chunk_count += 1
                        if chunk_count % 10 == 0:
                            print(f"Received {chunk_count} binary chunks...")
                    else:
                        # Probably JSON status
                        data = json.loads(message)
                        if data.get("status") == "done":
                            print("Received 'done' signal.")
                            break

            print(f"Success! WebSocket audio saved to {save_path}")
            print(f"Total chunks: {chunk_count}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_ws())
