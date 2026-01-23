# Use a stable Python image
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sox \
    libsox-fmt-all \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Install dependencies using uv
# --frozen ensures uv.lock is used without updates
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Place executable on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["python", "src/project/main.py"]
