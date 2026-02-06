# Stage 1: Builder (Large, uses devel image for compilation)
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Accelerate build
    uv_link_mode=copy

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    ca-certificates \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv via official installer script
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Create virtual environment with Python 3.12
RUN python3.12 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency definition
COPY pyproject.toml .

# Install dependencies into virtual environment
# We install with --no-cache to save build space
# Use /app/tmp as TMPDIR to avoid running out of space in /tmp during large wheel extraction
RUN mkdir -p /app/tmp && \
    TMPDIR=/app/tmp uv pip install --no-cache-dir -e ".[gpu-linux]" && \
    rm -rf /app/tmp

# Stage 2: Runtime (Small, uses runtime image)
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS runtime

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/app/.venv/bin:$PATH"

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
CMD ["uvicorn", "project.main:app", "--host", "0.0.0.0", "--port", "8000"]
