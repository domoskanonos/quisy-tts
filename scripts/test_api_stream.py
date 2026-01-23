import sys
from pathlib import Path

import requests


# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from project.config import ProjectConfig


settings = ProjectConfig.get_settings()
host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
ENDPOINT = f"http://{host}:{settings.PORT}/generate"
OUTPUT_DIR = settings.OUTPUT_DIR
HTTP_OK = 200


def test_stream() -> None:
    """Tests HTTP chunked streaming."""
    payload = {
        "text": "Dies ist ein Test des HTTP-Streamings. "
        "Wir empfangen die Audiodaten in kleinen Stücken.",
        "stream": True,
        "language_id": "de",
        "model_size": "0.6B",
    }
    print(f"Testing HTTP stream with {payload['model_size']} model...")

    try:
        with requests.post(ENDPOINT, json=payload, stream=True) as r:
            if r.status_code == HTTP_OK:
                save_path = OUTPUT_DIR / "test_stream_output.raw"
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

                with save_path.open("wb") as f:
                    chunk_count = 0
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            chunk_count += 1
                            if chunk_count % 10 == 0:
                                print(f"Received {chunk_count} chunks...")

                print(f"Success! Raw PCM audio saved to {save_path}")
                print(f"Total chunks: {chunk_count}")
            else:
                print(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_stream()
