"""CLI helper to run the app in development mode with hot reload.

Loads optional `.env` variables (via python-dotenv) and starts uvicorn.

Environment variables supported (defaults shown):
- UV_HOST (falls back to HOST) -> 127.0.0.1
- UV_PORT (falls back to PORT) -> 8000
- UV_RELOAD -> true/false (default: true)
- UV_RELOAD_DIRS -> comma-separated dirs to watch (optional)
- UV_RELOAD_EXCLUDES -> comma-separated glob patterns to ignore (optional)
- UV_RELOAD_DELAY -> float seconds delay (default: 0.25)
- UV_LOG_LEVEL -> info/debug/warning (default: info)
"""

from __future__ import annotations

import os
import typing

import uvicorn

# Load .env if present so developers can configure reload via .env
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # python-dotenv is optional for runtime; env vars still work
    pass

import sys
from pathlib import Path

# Ensure `src/` is on sys.path so `import api` works when this module
# is executed as an installed script (the working directory may differ).
_this_dir = Path(__file__).resolve().parent
if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

from api import app


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _split_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [p.strip() for p in value.split(",") if p.strip()]


def run() -> None:
    host = os.getenv("UV_HOST") or os.getenv("HOST") or "127.0.0.1"
    port = int(os.getenv("UV_PORT") or os.getenv("PORT") or 8000)

    reload_flag = _to_bool(os.getenv("UV_RELOAD"), True)
    reload_dirs = _split_list(os.getenv("UV_RELOAD_DIRS"))
    reload_excludes = _split_list(os.getenv("UV_RELOAD_EXCLUDES"))
    reload_delay = float(os.getenv("UV_RELOAD_DELAY") or 0.25)
    log_level = os.getenv("UV_LOG_LEVEL") or "info"

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload_flag,
        reload_dirs=reload_dirs,
        reload_excludes=reload_excludes,
        reload_delay=reload_delay,
        log_level=log_level,
    )


if __name__ == "__main__":
    run()
