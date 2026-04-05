# Quisy TTS 🚀

Quisy TTS is a modern, high-performance Text-to-Speech library powered by **Qwen3-TTS**. It supports voice cloning, instructed voice design, and custom speakers.

---

## 📦 Installation (PyPI)

You can install Quisy TTS directly from PyPI using your preferred Python package manager:

```bash
# Using pip
pip install quisy-tts

# Using uv
uv add quisy-tts
```

---

## ✨ Features

- **Qwen3-TTS Powered**: Utilizes the state-of-the-art Qwen3-TTS models.
- **Multiple Generation Modes**:
  - **Base (Voice Cloning)**: Clone any voice with just a short reference audio.
  - **VoiceDesign**: Generate voices based on natural language instructions.
  - **CustomVoice**: High-quality generation using pre-defined speaker IDs.
- **Optimized for GPU**: Native CUDA support with automatic fallback to CPU.
- **MCP Native**: Includes a built-in MCP server for direct interaction with LLM agents.

---

## 🤖 MCP Usage

Quisy TTS includes a built-in MCP server that allows LLMs to interact with TTS features directly using natural language.

### Usage with MCP Clients (Cursor, Claude Desktop)
After installing the package via PyPI, you can run the MCP server using `uvx` (to execute without full installation) or directly via the command installed with the package:

#### Option 1: Via `uvx` (Recommended)
Configure your MCP client to use the `uvx` command to run the tool:

- **Command**: `uvx`
- **Args**: `quisy-tts`

#### Option 2: Installed directly
If you have installed the package in your environment:

- **Command**: `quisy-tts-mcp`

---

## ⚙️ Configuration

All settings are managed via environment variables:

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
