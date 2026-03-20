"""FastAPI application setup with exception handlers and lifespan."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes import base, custom_voice, info, voice_design, voices_crud, websocket
from config import ProjectConfig

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


def _validate_startup_requirements() -> None:
    """Validate that all required dependencies are available. Raises RuntimeError if not."""
    import subprocess

    import torch

    # 1. Check qwen-tts
    try:
        import qwen_tts  # noqa: F401

        logger.info("✓ qwen-tts is available.")
    except ImportError as e:
        raise RuntimeError("qwen-tts is required but not installed. Install it with: pip install qwen-tts") from e

    # 2. Check sox binary
    try:
        result = subprocess.run(["sox", "--version"], capture_output=True, text=True, check=False)
        sox_version = result.stdout.strip() or result.stderr.strip()
        logger.info(f"✓ sox is available: {sox_version}")
    except FileNotFoundError as e:
        raise RuntimeError("sox is required but not found in PATH. Install it with: apt-get install sox") from e

    # 3. Check CUDA GPU
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU is required but not available. "
            "Ensure NVIDIA drivers and CUDA toolkit are installed, "
            "and run the container with --gpus all."
        )

    gpu_name = torch.cuda.get_device_name(0)
    logger.info(f"✓ CUDA GPU available: {gpu_name}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application lifecycle."""
    # Validate mandatory requirements before anything else
    _validate_startup_requirements()

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
    settings.APP_DIR.mkdir(parents=True, exist_ok=True)

    # Trigger model loading in background to optimize startup time
    # This prevents blocking the server while the model loads (10s+)
    import asyncio

    from api.dependencies import get_tts_engine

    engine = get_tts_engine()
    if hasattr(engine, "ensure_loaded"):
        # Preload the most commonly used model in background
        asyncio.create_task(engine.ensure_loaded("voice_design"))

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
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# API Routes
# =============================================================================


api_router = APIRouter()
api_router.include_router(info.router)
api_router.include_router(base.router, prefix="/generate/base")
api_router.include_router(voice_design.router, prefix="/generate/voice-design")
api_router.include_router(custom_voice.router, prefix="/generate/custom-voice")
api_router.include_router(voices_crud.router, prefix="/voices")
api_router.include_router(websocket.router)

app.include_router(api_router, prefix="/api")


# =============================================================================
# Static Files & UI
# =============================================================================


static_dir = Path(__file__).parent.parent / "static" / "ui"


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to /ui."""
    return RedirectResponse(url="/ui")


# Mount static files (will serve index.html for /ui)
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Deep link support for Angular SPA."""
    if request.url.path.startswith("/ui") and static_dir.exists():
        return FileResponse(static_dir / "index.html")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
