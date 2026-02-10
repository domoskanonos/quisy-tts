# Quisy TTS

Quisy TTS is a modern, high-performance Text-to-Speech API powered by **Qwen3-TTS**, supporting advanced features like voice cloning, instructed voice design, and real-time streaming.

## Quick Start

### Basic Usage (CPU/GPU)

```bash
docker run -d \
  -p 8000:8000 \
  --gpus all \
  --name quisy-tts \
  domoskanonos/quisy-tts:latest
```

### With Volume Persistence (Recommended)

Keep your models and outputs persistent:

```bash
docker run -d \
  --gpus all \
  -p 8000:8000 \
  -v quisy_models:/app/models \
  -v quisy_output:/app/output \
  --name quisy-tts \
  domoskanonos/quisy-tts:latest
```

## Docker Compose

```yaml
services:
  tts:
    image: domoskanonos/quisy-tts:latest
    ports:
      - "8000:8000"
    environment:
      - DEVICE=cuda
    volumes:
      - ./models:/app/models
      - ./output:/app/output
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `DEVICE` | Computation device (`cuda` or `cpu`) | `cuda` |
| `HOST` | API listening host | `0.0.0.0` |
| `PORT` | API listening port | `8000` |

## Tags

- `latest`: The latest stable build.
- `cuda-*`: Builds specifically targeting CUDA versions.
