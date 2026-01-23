"""FastAPI application setup with exception handlers and lifespan."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import JSONResponse

from project.api.dependencies import get_cleanup_service
from project.api.routes import base, custom_voice, voice_design, websocket
from project.config import ProjectConfig
from project.core import CleanupService


logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application lifecycle."""
    # Startup
    logger.info("Registered Routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            logger.info(f" -> {methods} {route.path}")
        else:
            logger.info(f" -> {route.path}")

    # Ensure directories exist
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.VOICES_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="Cosmo TTS API",
    description=(
        "Production-ready Text-to-Speech API powered by Qwen3-TTS. "
        "Supports base (voice cloning), voice design, and custom voice modes."
    ),
    version="3.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Global Exception Handlers
# =============================================================================


@app.exception_handler(ValueError)
async def validation_exception_handler(
    _request: object, exc: ValueError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(RuntimeError)
async def runtime_exception_handler(
    _request: object, exc: RuntimeError
) -> JSONResponse:
    """Handle runtime errors (e.g., model loading failures)."""
    logger.error(f"Runtime error: {exc}")
    return JSONResponse(status_code=503, content={"detail": "TTS engine unavailable"})


# =============================================================================
# Include Routers
# =============================================================================


app.include_router(base.router, prefix="/generate/base")
app.include_router(voice_design.router, prefix="/generate/voice-design")
app.include_router(custom_voice.router, prefix="/generate/custom-voice")
app.include_router(websocket.router)


# =============================================================================
# Root & Utility Endpoints
# =============================================================================


@app.get("/")
def read_root() -> dict[str, Any]:
    """Returns the API status."""
    return {
        "message": "Cosmo TTS API is running",
        "version": "3.0.0",
        "architecture": "Clean Architecture (Hexagonal)",
        "available_endpoints": [
            "/generate/base/0.6b",
            "/generate/base/1.7b",
            "/generate/voice-design/1.7b",
            "/generate/custom-voice/0.6b",
            "/generate/custom-voice/1.7b",
        ],
    }


@app.post("/cleanup", response_model=None)
async def trigger_cleanup(
    background_tasks: BackgroundTasks,
    max_age_hours: int = 24,
    cleanup: CleanupService = Depends(get_cleanup_service),
) -> dict[str, str]:
    """Trigger cleanup of old audio files."""
    background_tasks.add_task(
        cleanup.cleanup_old_files, settings.OUTPUT_DIR, max_age_hours
    )
    return {"status": "Cleanup scheduled"}
