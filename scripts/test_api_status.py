import requests


ENDPOINT = "http://localhost:8000/"


def test_status() -> None:
    """Checks the API status endpoint."""
    try:
        print(f"Testing API status at {ENDPOINT}...")
        response = requests.get(ENDPOINT)

        if response.status_code == 200:
            data = response.json()
            print("Success! API is running.")
            print(f"Response: {data}")
        else:
            print(f"Failed: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Is the server running?")


if __name__ == "__main__":
    test_status()
