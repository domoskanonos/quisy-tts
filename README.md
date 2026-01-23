# Cosmo TTS 🚀

[![Pipeline](https://github.com/domoskanonos/cosmo-tts/actions/workflows/pipeline.yml/badge.svg)](https://github.com/domoskanonos/cosmo-tts/actions/workflows/pipeline.yml)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Cosmo TTS is a modern, high-performance Text-to-Speech API powered by **Qwen3-TTS**. It supports advanced features like voice cloning, instructed voice design, and real-time streaming via WebSockets and HTTP.

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
- **Sox Integration**: High-quality audio post-processing (normalization, equalization).

---

## 🛠 Prerequisites

This project requires **uv**. If you don't have it installed:

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 🔊 Audio Processing (Sox)
This project requires **Sox** for high-quality audio normalization.
- **Windows**: `scoop install sox`, `choco install sox`, or download from [SourceForge](http://sox.sourceforge.net/).
- **macOS**: `brew install sox`
- **Linux**: `sudo apt install sox libsox-fmt-all`

---

## 🚀 Quick Start

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/domoskanonos/cosmo-tts.git
   cd cosmo-tts
   uv sync
   ```

2. **Configure**:
   Create a `.env` file (copied from the example in the docs or starting from scratch):
   ```bash
   LOG_LEVEL=INFO
   DEFAULT_MODEL_SIZE=0.6B
   DEVICE=cuda
   HOST=0.0.0.0
   PORT=8000
   ```

3. **Download Models**:
   ```bash
   uv run python scripts/download_models.py
   ```

4. **Run the API**:
   ```bash
   uv run python src/project/main.py
   ```

---

## ⚙️ Configuration

All settings are managed via Pydantic and can be overridden by environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Name of the service | `cosmo-tts` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DEVICE` | Computation device (`cuda` or `cpu`) | `cuda` |
| `HOST` | API listening host | `0.0.0.0` |
| `PORT` | API listening port | `8000` |
| `DEFAULT_MODEL_SIZE` | Default model variant (`1.7B` or `0.6B`) | `1.7B` |
| `MODELS_DIR` | Directory to store model checkpoints | `models` |
| `VOICES_DIR` | Directory for reference audio files | `voices` |
| `OUTPUT_DIR` | Directory for generated audio files | `output` |

---

## 🔌 API Endpoints

### `POST /generate`
Generates audio from text. Supports both file transfer and streaming.
- **Payload**: `GenerateRequest` (JSON)
- **Streaming**: Set `"stream": true` to receive chunked raw PCM data (int16).

### `WS /ws`
Real-time WebSocket endpoint. Send JSON payloads and receive binary audio chunks.

### `GET /status`
Check the health and configuration of the API.

---

## 🧪 Testing

We provide dedicated scripts to test all generation modes:

```bash
# Test API Generation (Standard)
uv run python scripts/test_api_generate.py

# Test HTTP Streaming
uv run python scripts/test_api_stream.py

# Test WebSocket Streaming
uv run python scripts/test_api_ws.py

# Verify all model modes
uv run python tests/verify_modes.py
```

---

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
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
