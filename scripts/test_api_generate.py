import sys
from pathlib import Path

import requests  # type: ignore[import]


# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig


settings = ProjectConfig.get_settings()
host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
ENDPOINT = f"http://{host}:{settings.PORT}/generate"
OUTPUT_DIR = settings.OUTPUT_DIR
HTTP_OK = 200


def test_generate(
    text: str,
    mode: str = "base",
    size: str = "1.7B",
    instruct: str | None = None,
    speaker: str | None = None,
) -> None:
    """Sends a generation request to the API and saves the output."""
    payload = {
        "text": text,
        "mode": mode,
        "model_size": size,
        "instruct": instruct,
        "speaker": speaker,
        "language_id": "de",
    }

    print(f"Testing {size} {mode} mode...")
    response = requests.post(ENDPOINT, json=payload)

    if response.status_code == HTTP_OK:
        filename = response.headers.get("Content-Disposition", "").split("filename=")[-1] or "output.wav"
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        save_path = OUTPUT_DIR / filename
        save_path.write_bytes(response.content)
        print(f"Success! Audio saved to {save_path}")
    else:
        print(f"Failed: {response.status_code} - {response.text}")


if __name__ == "__main__":
    # Test 1.7B Models (All modes supported)
    test_generate("This is a test of the 1.7B Base model.", mode="base", size="1.7B")
    test_generate(
        "I am an excited reporter reporting live!",
        mode="voice_design",
        size="1.7B",
        instruct="an excited reporter",
    )
    test_generate(
        "Hello from Eric, running on the 1.7B model.",
        mode="custom_voice",
        size="1.7B",
        speaker="eric",
    )

    # Test 0.6B Models (VoiceDesign not supported/downloaded)
    test_generate("Dies ist ein Test der 0.6B Basis-Stimme.", mode="base", size="0.6B")
    test_generate(
        "Hallo von Eric, auf dem 0.6B Modell.",
        mode="custom_voice",
        size="0.6B",
        speaker="eric",
    )
    # Note: 0.6B VoiceDesign is skipped as it appears unavailable
