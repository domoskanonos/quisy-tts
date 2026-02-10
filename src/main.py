"""Cosmo TTS - Entry point.

This is a minimal entry point that imports and runs the FastAPI application.
All application logic is organized in the following layers:

- api/        : Presentation layer (routes, dependencies)
- core/       : Domain layer (interfaces, exceptions)
- services/   : Application layer (use cases)
- engine/     : Infrastructure layer (TTS adapters)
- audio/      : Infrastructure layer (audio processing)
- models/     : Model management
- schemas/    : Data transfer objects
"""

import uvicorn

from api import app
from config import ProjectConfig


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


def main() -> None:
    """Start the FastAPI server."""
    logger.info(f"Starting {settings.PROJECT_NAME} on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    main()
