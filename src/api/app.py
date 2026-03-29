"""FastAPI application setup with exception handlers and lifespan."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.routing import APIRoute
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

    # Startup
    logger.info("Application starting...")
    settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    settings.VOICES_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure all voices in the DB have reference audio. If audio is missing
    # generation will be attempted synchronously at startup so subsequent API
    # calls can rely on presence of reference audio.
    try:
        from services.voice_service import VoiceService
        from api.dependencies import get_tts_service
        import asyncio

        vs = VoiceService()
        tts = get_tts_service()
        voices = vs.list_voices()
        logger.info(f"Startup integrity: found {len(voices)} voices in database. VOICES_DIR={settings.VOICES_DIR}")
        logger.debug("Voice IDs: %s", [v.get("voice_id") for v in voices])

        # Direct integrity check: generate missing reference audio sequentially.
        # Check for missing physical files (voice_<id>.wav) instead of relying on DB column.
        voices_to_generate: list[str] = []
        for v in voices:
            vid = v.get("voice_id") or v.get("voiceId") or v.get("id")
            if not vid:
                continue
            audio_path = settings.VOICES_DIR / f"voice_{vid}.wav"
            if not audio_path.exists() or audio_path.stat().st_size == 0:
                voices_to_generate.append(vid)
        logger.info(f"Startup integrity: voices_to_generate={len(voices_to_generate)}")

        if voices_to_generate:
            logger.info(f"Integrity check: generating reference audio for {len(voices_to_generate)} voices...")
            for voice_id in voices_to_generate:
                logger.info(f"Generating reference audio for voice: {voice_id}")
                try:
                    await tts.voice_audio_integrity.ensure_audio(voice_id, tts.generate_audio)
                except Exception as e:
                    logger.error(f"Failed to generate reference audio for {voice_id}: {e}")
                    # Continue to attempt others but fail startup if any generation fails
                    raise
            logger.info("Integrity check completed successfully.")

    except Exception as e:
        logger.error(f"Startup voice audio verification failed: {e}")
        # Terminate to fail-fast
        raise SystemExit(f"Startup failed due to voice integrity issue: {e}") from e

    yield

    # Shutdown
    logger.info("Application shutting down...")


app: FastAPI = FastAPI(
    title="Cosmo TTS API",
    description="Production-ready Text-to-Speech API.",
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
async def root_redirect() -> RedirectResponse:
    """Redirect root to /ui."""
    return RedirectResponse(url="/ui")


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
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse | FileResponse:
    """Deep link support for Angular SPA."""
    if request.url.path.startswith("/ui") and static_dir.exists():
        return FileResponse(static_dir / "index.html")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
