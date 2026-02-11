# Cosmo TTS - Advanced Text-to-Speech Engine

[![Docker Image Size (latest)](https://img.shields.io/docker/image-size/domoskanonos/quisy-tts/latest?style=flat-square)](https://hub.docker.com/r/domoskanonos/quisy-tts)
[![Docker Pulls](https://img.shields.io/docker/pulls/domoskanonos/quisy-tts?style=flat-square)](https://hub.docker.com/r/domoskanonos/quisy-tts)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

**Cosmo TTS** is a high-performance, open-source Text-to-Speech engine powered by **Qwen2-Audio** and **Qwen2.5-LLM**. It delivers state-of-the-art voice synthesis with features like voice cloning, cross-lingual support, and ultra-low latency streaming.

## 🚀 Key Features

- **SoTA Quality**: leverage Qwen2-Audio for natural, expressive speech.
- **Voice Cloning**: Zero-shot voice cloning from a short reference audio (5-10s).
- **Dual Backend**:
    - **Transformers**: Compatible with Windows/CPU/CUDA.
    - **vLLM (Linux/WSL)**: High-throughput, optimized inference for production.
- **Streaming API**: Real-time audio streaming via HTTP and WebSocket.
- **OpenAI Compatible**: Drop-in replacement for OpenAI's audio API (in progress).

---

## 📦 Quick Start

### 1. Run with Docker (Recommended)

The easiest way to run Cosmo TTS is using Docker. We provide a pre-built image optimized for CUDA.

**Prerequisites:**
- NVIDIA GPU with drivers installed
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

```bash
docker run -d --gpus all -p 8000:8000 --name quisy-tts domoskanonos/quisy-tts:latest
```

### 2. Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
services:
  tts:
    image: domoskanonos/quisy-tts:latest
    ports:
      - "8000:8000"
    volumes:
      - ./voices:/app/voices
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - DEVICE=cuda
      - MODEL_SIZE=small  # or 'medium', 'large'
```

Then run:

```bash
docker compose up -d
```

---

## 🛠 Configuration

Configure the engine using environment variables:

| Variable | Default | Description |
|---|---|---|
| `DEVICE` | `cuda` | Hardware to use: `cuda`, `cpu`. |
| `MODEL_SIZE` | `small` | Model size to load. |
| `Use_VLLM` | `false` | Enable vLLM backend (Linux only, requires `vllm` package). |
| `DEFAULT_LANGUAGE` | `en` | Default language for synthesis. |
| `VOICES_DIR` | `/app/voices` | Directory to store reference voices. |

---

## 📡 API Usage

### Text-to-Speech (Simple)

```bash
curl -X POST "http://localhost:8000/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, world! This is Cosmo TTS speaking.",
    "voice": "nova"
  }' \
  --output speech.wav
```

### Voice Cloning

```bash
curl -X POST "http://localhost:8000/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "This voice is cloned from the reference audio.",
    "voice": "cloned-voice",
    "reference_audio": "path/to/reference.wav"
  }' \
  --output cloned_speech.wav
```

---

## 🔧 Building Locally

To build the image yourself:

```bash
git clone https://github.com/domoskanonos/quisy-tts.git
cd quisy-tts
docker build -t quisy-tts .
```

---

## 📄 License

This project is licensed under the MIT License.
