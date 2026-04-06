# 03. System Scope and Context

## Business Context
Quisy TTS acts as a high-performance, streaming-capable TTS provider, enabling applications to generate natural-sounding speech from text using instruction-based design and voice cloning.

## Technical Context
The system interfaces with:
*   **Clients:** HTTP and WebSocket clients requesting speech synthesis.
*   **TTS Model Backend:** Executes the actual inference (e.g., Qwen3-TTS).
*   **Local Storage:** Persistent data for models, voices, and generated audio.
