"""FastAPI application setup with exception handlers and lifespan."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.routes import base, custom_voice, info, voice_design, websocket
from config import ProjectConfig


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
            path = getattr(route, "path", str(route))
            logger.info(f" -> {methods} {path}")
        else:
            path = getattr(route, "path", str(route))
            logger.info(f" -> {path}")

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
async def validation_exception_handler(_request: object, exc: ValueError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(RuntimeError)
async def runtime_exception_handler(_request: object, exc: RuntimeError) -> JSONResponse:
    """Handle runtime errors (e.g., model loading failures)."""
    logger.error(f"Runtime error: {exc}")
    return JSONResponse(status_code=503, content={"detail": "TTS engine unavailable"})


# =============================================================================
# Include Routers
# =============================================================================


app.include_router(info.router)
app.include_router(base.router, prefix="/generate/base")
app.include_router(voice_design.router, prefix="/generate/voice-design")
app.include_router(custom_voice.router, prefix="/generate/custom-voice")
app.include_router(websocket.router)
