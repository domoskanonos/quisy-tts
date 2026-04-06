"""FastAPI application setup with exception handlers and lifespan."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import audio_processing, generate, info, voices_crud, voices_search, websocket
from config import ProjectConfig
from mcp_server import mcp

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


# =============================================================================
# Lifespan
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application lifecycle."""
    # Validate mandatory requirements before anything else
    # _validate_startup_requirements() # Uncomment if you have this function

    # Startup: create directories and write a startup marker. Heavy integrity
    # generation is intentionally postponed to a background task so the API
    # becomes responsive immediately.
    logger.info("Application starting...")
    try:
        settings.APP_DIR.mkdir(parents=True, exist_ok=True)
        startup_log = settings.APP_DIR / "startup.log"
        with open(startup_log, "a", encoding="utf-8") as fh:
            fh.write("Application starting...\n")
    except Exception:
        logger.debug("Failed to write startup marker to disk")

    settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    settings.VOICES_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("Application shutting down...")


app: FastAPI = FastAPI(
    title="Cosmo TTS API",
    description=(
        "Production-ready Text-to-Speech API using Qwen-TTS models (1.7B/0.6B).\n\n"
        "### Key Features\n"
        "* **High-Quality TTS**: Generate speech from text with automatic style application based on selected voices.\n"
        "* **Voice Cloning**: Use reference WAV files for highly accurate voice imitation.\n"
        "* **Voice Design**: Create new voices from natural language descriptions (requires 1.7B model).\n"
        "* **SSML Engine**: Advanced support for multiple speakers, breaks, and expressive control via markup.\n"
        "* **Smart Voice Management**: Full CRUD for voices, including advanced FTS5-based searching and style term discovery.\n"
        "* **Audio Processing**: Utilities for uploading temporary audio and concatenating multiple files into one.\n\n"
        "### Usage Guidelines\n"
        "* **Language Format**: Always use full language names (e.g., `'german'`, `'english'`) instead of short codes.\n"
        "* **Automatic Styles**: For standard generation, `instruct` tags are automatically retrieved from the database to match the voice's unique character.\n"
        "* **API Prefix**: All functional endpoints are prefixed with `/api`."
    ),
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


# Note: background reference-audio generation intentionally disabled.
# Missing reference audio will be generated on-demand when a generation
# request arrives (via VoiceAudioIntegrityService.ensure_audio).


# CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API Routes
# =============================================================================


api_router = APIRouter()
api_router.include_router(audio_processing.router, prefix="/audio")
api_router.include_router(info.router)
api_router.include_router(generate.router, prefix="/generate")
api_router.include_router(voices_search.router, prefix="/voices")
api_router.include_router(voices_crud.router, prefix="/voices")
api_router.include_router(websocket.router)

app.include_router(api_router, prefix="/api")


# =============================================================================
# Static Files & UI
# =============================================================================


static_dir = Path(__file__).parent.parent / "static" / "ui"


@app.get("/", include_in_schema=False)
async def root_info():
    """Root endpoint — return a small JSON payload (no redirect).

    This avoids redirecting to a possibly-missing UI and is friendlier for
    automated health checks and API clients.
    """
    return JSONResponse(
        status_code=200, content={"status": "ok", "message": "API running. Open /api/docs for Swagger UI."}
    )


# Mount static files (will serve index.html for /ui)
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")

# Mount generated audio files to make them accessible via URL
app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")


# Mount MCP server under /mcp to avoid shadowing the API routes when the
# MCP application is present. This keeps the API available at /api for tests
# and clients while still exposing the MCP UI under /mcp.
mcp_app = mcp.http_app()
app.mount("/interface", mcp_app)

# Integrate lifespan context from MCP app if present (best-effort).
try:
    app.router.lifespan_context = mcp_app.router.lifespan_context
except Exception:
    # If MCP app doesn't expose lifespan_context, ignore.
    pass


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return JSON 404 for missing endpoints (no SPA redirect)."""
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
