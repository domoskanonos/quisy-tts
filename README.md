# Quisy TTS 🚀

[![Pipeline](https://github.com/domoskanonos/quisy-tts/actions/workflows/pipeline.yml/badge.svg)](https://github.com/domoskanonos/quisy-tts/actions/workflows/pipeline.yml)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Quisy TTS is a modern, high-performance Text-to-Speech API powered by **Qwen3-TTS**. It supports voice cloning, instructed voice design, custom (predefined) speakers, and real-time streaming via WebSockets and HTTP.

---

## ✨ Features

- **Qwen3-TTS Powered**: Utilizes the state-of-the-art Qwen3-TTS models (1.7B and 0.6B versions).
- **Multiple Generation Modes**:
  - **Base (Voice Cloning)**: Clone any voice with just a short reference audio.
  - **VoiceDesign**: Generate voices based on natural language instructions (e.g., "an excited reporter").
  - **CustomVoice**: High-quality generation using pre-defined speaker IDs.
- **Streaming Support**:
  - **HTTP Chunked**: Receive audio data as a stream for immediate playback.
  - **WebSocket**: Full-duplex real-time TTS generation.
- **Optimized for GPU**: Native CUDA support with automatic fallback to CPU.
- **Modern Stack**: Built with FastAPI, Pydantic Settings, and [uv](https://github.com/astral-sh/uv).
---

## 🛠 Prerequisites

This project requires **uv**. If you don't have it installed:

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 🔊 Requirements
The application performs runtime validations on startup and will fail early if mandatory dependencies are missing. The most important requirements are:

- `qwen-tts` Python package (model runtime adapter). Install with `pip install qwen-tts`.
- CUDA-capable NVIDIA GPU and matching `torch` build when running on `DEVICE=cuda`. The application currently checks `torch.cuda.is_available()` at startup and will raise an error if a CUDA device is required but not available.

If you want to run without GPU in development, set `DEVICE=cpu`, but note that performance and some generation modes may be substantially slower or unsupported depending on available models.

---

## 🚀 Quick Start

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/domoskanonos/quisy-tts.git
   cd quisy-tts
   uv sync
   ```

2. **Configure**:
   Create a `.env` file (copied from the example in the docs or starting from scratch):
   ```bash
   LOG_LEVEL=INFO
   DEVICE=cuda
   HOST=0.0.0.0
   PORT=8045
   ```

3. **Download Models**:
   ```bash
   uv run python scripts/download_models.py
   ```

4. **Run the API (development with hot reload)**:
   You can now start the backend in dev mode via `uv` and enable hot reload.

   - Using environment variables directly (PowerShell example):
     ```powershell
     $env:UV_HOST = '0.0.0.0'; $env:UV_PORT = '8050'; uv run start-dev
     ```

   - Or create a `.env` file in the project root and set overrides there. Supported variables:
     - `UV_HOST` / `HOST` - bind address (default `127.0.0.1`)
     - `UV_PORT` / `PORT` - port (default `8045`)
     - `UV_RELOAD` - enable/disable reload (`true`/`false`, default `true`)
     - `UV_RELOAD_DIRS` - comma-separated directories to watch for reloads
     - `UV_RELOAD_EXCLUDES` - comma-separated glob patterns to ignore
     - `UV_RELOAD_DELAY` - debounce delay in seconds for reloads (default `0.25`)
     - `UV_LOG_LEVEL` - uvicorn log level (default `info`)

     Example `.env`:
     ```text
     UV_HOST=0.0.0.0
     UV_PORT=8050
     UV_RELOAD=true
     UV_RELOAD_DIRS=src,api
     UV_LOG_LEVEL=debug
     ```

    - Then run:
      ```bash
      uv run start-dev
      ```

    Development frontend (Angular)
    --------------------------------

    - Create a proxy file `frontend/proxy.local.json` (example below) and adjust `target` to your backend port.
      ```json
      {
        "/api": {
          "target": "http://localhost:8045",
          "secure": false,
          "changeOrigin": true,
          "logLevel": "debug"
        },
        "/ws": {
          "target": "ws://localhost:8045",
          "ws": true,
          "secure": false,
          "changeOrigin": true,
          "logLevel": "debug"
        }
      }
      ```

    - Install frontend deps and start with the proxy (from the `frontend` folder):
      ```bash
      cd frontend
      npm install
      npm run start -- --proxy-config proxy.local.json
      # or: npx ng serve --proxy-config proxy.local.json
      ```

    - If you prefer to make the proxy permanent for `npm run start`, update `frontend/package.json` start script to:
      ```json
      "start": "ng serve --proxy-config proxy.local.json"
      ```

5. **Docker Usage**:
   We provide a pre-built Docker image.

   **Pull:**
   ```bash
   docker pull domoskanonos/quisy-tts:latest
   ```

   **Run (GPU Recommended):**
   ```bash
   docker run -d --gpus all -p 8045:8045 --name quisy-tts \
     -v ${PWD}/models:/app/models \
     -v ${PWD}/output:/app/output \
     domoskanonos/quisy-tts:latest
   ```

---

## 🤖 MCP Server (Model Context Protocol)

Quisy TTS includes a built-in MCP server that allows LLMs to interact with TTS features directly using natural language.

### Usage

The MCP server is hosted at `/mcp` on your running Quisy TTS instance. 

#### Local Development
1. Ensure your API server is running (see [Quick Start](#🚀-quick-start)).
2. Configure your MCP client (e.g., Claude Desktop, Cursor) to connect to:
   - **Transport**: SSE (Server-Sent Events)
   - **URL**: `http://localhost:8045/mcp/sse`

#### Docker Usage
If running via Docker, ensure the container port is exposed:
```bash
docker run -d --gpus all -p 8045:8045 --name quisy-tts \
  -v ${PWD}/models:/app/models \
  -v ${PWD}/output:/app/output \
  domoskanonos/quisy-tts:latest
```
Then configure your MCP client to use `http://localhost:8045/mcp/sse`.

---

## ⚙️ Configuration

All settings are managed via Pydantic and can be overridden by environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Name of the service | `quisy-tts` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DEVICE` | Computation device (`cuda` or `cpu`) | `cuda` |
| `HOST` | API listening host | `0.0.0.0` |
| `PORT` | API listening port | `8045` |
| `MODELS_DIR` | Directory to store model checkpoints | `models` |
| `VOICES_DIR` | Directory for reference audio files | `voices` |
| `AUDIO_DIR` | Directory for generated audio files | `audio` |
| `APP_DIR` | Application data directory (preload/cache) | `database` |

---

## 🔌 API Endpoints

### Base Mode (Voice Cloning)
- `POST /generate/base/0.6b` / `1.7b`
- `POST /generate/base/stream/0.6b` / `1.7b`

### Voice Design (Text-to-Speech with Instruction)
- `POST /generate/voice-design/1.7b` (0.6B not supported)
- `POST /generate/voice-design/stream/1.7b`

### Custom Voice (Predefined Speakers)
- `POST /generate/custom-voice/0.6b` / `1.7b`
- `POST /generate/custom-voice/stream/0.6b` / `1.7b`

### Voice Management (CRUD & Audio)
- `GET /voices/` — list available voices (including built-in defaults)
- `GET /voices/{voice_id}` — retrieve voice metadata
- `POST /voices/` — create voice metadata (upload audio separately)
- `PUT /voices/{voice_id}` — update voice metadata
- `DELETE /voices/{voice_id}` — delete a non-default voice
- `POST /voices/{voice_id}/audio` — upload or replace the audio file for a voice
- `GET /voices/{voice_id}/audio` — download the voice example audio
- `POST /voices/{voice_id}/ensure-audio` — trigger background generation of example audio (returns 202)

### WebSocket
Real-time streaming endpoint:
- `WS /ws/0.6b` or `/ws/1.7b`

### Health
- `GET /status`

---


## 📖 API Documentation

FastAPI automatically generates interactive documentation for the API:

- **Swagger UI**: [http://localhost:8045/docs](http://localhost:8045/docs) - Test the API directly from your browser.
- **ReDoc**: [http://localhost:8045/redoc](http://localhost:8045/redoc) - Clean, searchable documentation.
- **OpenAPI JSON**: [http://localhost:8045/openapi.json](http://localhost:8045/openapi.json)


## 🛠 Development

### Quality Checks
```bash
# Linting & Formatting
uv run ruff check .
uv run ruff format .

# Type Checking
uv run mypy .

# Tests
uv run pytest

# Pre-commit Hooks
uv run pre-commit install --hook-type commit-msg --hook-type pre-commit
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
