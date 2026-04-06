# 02. Architecture Constraints

## Technical Constraints
*   **Language:** Python 3.12+
*   **Framework:** FastAPI for the web API layer.
*   **Database:** SQLite for lightweight, file-based metadata storage.
*   **Concurrency:** `asyncio` for non-blocking I/O operations (crucial for streaming).
*   **Deployment:** Docker containers; CI/CD via GitHub Actions.
*   **Dependencies:** Management via `uv`.

## Organizational Constraints
*   **License:** MIT License.
*   **Documentation:** Arc42 standards.

## Environment Constraints
*   **Hardware:** Requires CUDA-capable NVIDIA GPU for optimal performance (using `qwen-tts` and `torch`), with CPU fallback (for development/testing only).
