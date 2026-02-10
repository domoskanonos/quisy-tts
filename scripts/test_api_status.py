import sys
from pathlib import Path

import requests


# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig


settings = ProjectConfig.get_settings()
host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
ENDPOINT = f"http://{host}:{settings.PORT}/"
HTTP_OK = 200


def test_status() -> None:
    """Checks the API status endpoint."""
    try:
        print(f"Testing API status at {ENDPOINT}...")
        response = requests.get(ENDPOINT)

        if response.status_code == HTTP_OK:
            data = response.json()
            print("Success! API is running.")
            print(f"Response: {data}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Is the server running?")


if __name__ == "__main__":
    test_status()
