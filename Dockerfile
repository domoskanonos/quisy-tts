# Stage 1: Builder
FROM ubuntu:22.04 AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install minimal build dependencies and Python 3.12
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    gnupg \
    build-essential \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment with Python 3.12
RUN python3.12 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

# Copy dependency definition
COPY pyproject.toml .

# Copy source code for installation
COPY src/ src/

# Install PyTorch with CUDA 12.1 support FIRST to ensure GPU version is used
RUN /app/.venv/bin/pip install --no-cache-dir \
    torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install vLLM-Omni and flash-attn (mandatory for GPU inference)
RUN /app/.venv/bin/pip install --no-cache-dir "vllm-omni>=0.7.0" "flash-attn>=2.0.0"

# Install remaining project dependencies (torch/vllm already satisfied from above)
RUN /app/.venv/bin/pip install --no-cache-dir .

# Stage 2: Runtime (uses NVIDIA runtime image for GPU inference)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS runtime

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

WORKDIR /app

# Install minimal runtime dependencies (python, audio libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    libsndfile1 \
    sox \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code and config
COPY src/ src/
COPY .env.example .env

# Expose API port
EXPOSE 8000

# Run commands
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
