# Quisy TTS 🚀

Quisy TTS is a modern, high-performance Text-to-Speech library powered by **Qwen3-TTS**. It supports voice cloning, instructed voice design, and custom speakers.

---

## ✨ Features

- **Qwen3-TTS Powered**: Utilizes the state-of-the-art Qwen3-TTS models (1.7B and 0.6B versions).
- **Multiple Generation Modes**:
  - **Base (Voice Cloning)**: Clone any voice with just a short reference audio.
  - **VoiceDesign**: Generate voices based on natural language instructions.
  - **CustomVoice**: High-quality generation using pre-defined speaker IDs.
- **Optimized for GPU**: Native CUDA support with automatic fallback to CPU.
- **MCP Native**: Includes a built-in MCP server for direct interaction with LLM agents.

---

## 🛠 Prerequisites

This project requires **uv**.

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 🚀 Quick Start

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/domoskanonos/quisy-tts.git
   cd quisy-tts
   uv sync
   ```

2. **Run the MCP Server**:
   You can run the MCP server directly using python:
   ```bash
   python src/mcp_server.py
   ```

   This will start the MCP server, ready for connection by your MCP client (e.g., Cursor, Claude Desktop).

---

## 🤖 MCP Server (Model Context Protocol)

Quisy TTS includes a built-in MCP server that allows LLMs to interact with TTS features directly using natural language.

### Usage with MCP Clients
Configure your MCP client to use the `mcp_server.py` file:

- **Command**: `python`
- **Args**: `[PATH_TO_PROJECT]/src/mcp_server.py`

---

## ⚙️ Configuration

All settings are managed via Pydantic and can be overridden by environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DEVICE` | Computation device (`cuda` or `cpu`) | `cuda` |
| `MODELS_DIR` | Directory to store model checkpoints | `models` |
| `VOICES_DIR` | Directory for reference audio files | `voices` |
| `AUDIO_DIR` | Directory for generated audio files | `audio` |

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
