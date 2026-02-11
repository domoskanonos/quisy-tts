# Stage 1: Builder (uses slim Python image for smaller footprint)
FROM python:3.12-slim AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    uv_link_mode=copy

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv via official installer script
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Create virtual environment with Python 3.12
RUN python3.12 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

# Copy dependency definition
COPY pyproject.toml .

# Copy source code for installation
COPY src/ src/

# Install core dependencies (without GPU extras to save space during build)
# Then install GPU extras separately, allowing flash-attn to fail gracefully
RUN /app/.venv/bin/pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu121 . && \
    /app/.venv/bin/pip install --no-cache-dir "vllm>=0.3.0" || true

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
