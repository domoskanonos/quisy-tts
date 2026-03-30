# Stage 1: Backend Builder
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_NO_CACHE=1 \
    TORCH_CUDA_ARCH_LIST="8.6"

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

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definition
COPY pyproject.toml uv.lock ./

# Install dependencies (including GPU extras)
RUN uv sync --frozen --no-dev --extra gpu --no-install-project

# Copy source code
COPY src/ src/
COPY README.md .

# Install project
RUN uv sync --frozen --no-dev --extra gpu

# Pre-install spaCy models
RUN .venv/bin/python -m ensurepip --upgrade && \
    .venv/bin/python -m pip install spacy && \
    .venv/bin/python -m spacy download de_core_news_sm && \
    .venv/bin/python -m spacy download en_core_web_sm

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
EXPOSE 8045

# Run commands
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8045"]
