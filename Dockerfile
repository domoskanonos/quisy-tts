# Use a slim Python image
FROM python:3.14-slim-bookworm

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

# Run the application
CMD ["python", "src/project/main.py"]
