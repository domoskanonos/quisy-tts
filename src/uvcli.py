"""CLI helper to run the app in development mode with hot reload.

Loads optional `.env` variables (via python-dotenv) and starts uvicorn.

Environment variables supported (defaults shown):
- UV_HOST (falls back to HOST) -> 127.0.0.1
- UV_PORT (falls back to PORT) -> 8045
- UV_RELOAD -> true/false (default: true)
- UV_RELOAD_DIRS -> comma-separated dirs to watch (optional)
- UV_RELOAD_EXCLUDES -> comma-separated glob patterns to ignore (optional)
- UV_RELOAD_DELAY -> float seconds delay (default: 0.25)
- UV_LOG_LEVEL -> info/debug/warning (default: info)
"""

from __future__ import annotations

import os

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
    port = int(os.getenv("UV_PORT") or os.getenv("PORT") or 8045)

    reload_flag = _to_bool(os.getenv("UV_RELOAD"), True)
    # sensible defaults to avoid watching large output files
    reload_dirs = _split_list(os.getenv("UV_RELOAD_DIRS")) or [str(_this_dir.parent)]
    reload_excludes = _split_list(os.getenv("UV_RELOAD_EXCLUDES")) or ["output", "*.wav"]
    reload_delay = float(os.getenv("UV_RELOAD_DELAY") or 0.25)
    log_level = os.getenv("UV_LOG_LEVEL") or "info"

    # Ensure child reload processes can import the application package by
    # adding the `src/` directory to PYTHONPATH (uvicorn spawns subprocesses
    # for reload/workers that inherit environment variables).
    src_dir = str(_this_dir)
    prev_py = os.environ.get("PYTHONPATH", "")
    if src_dir not in prev_py.split(os.pathsep):
        os.environ["PYTHONPATH"] = (prev_py + os.pathsep + src_dir).lstrip(os.pathsep)

    # Pass the application as an import string so uvicorn's reloader can
    # import it in child processes: module:path (api.app:app)
    try:
        uvicorn.run(
            "api.app:app",
            host=host,
            port=port,
            reload=reload_flag,
            reload_dirs=reload_dirs,
            reload_excludes=reload_excludes,
            reload_delay=reload_delay,
            log_level=log_level,
        )
    except OSError:
        # Provide a more actionable error message for common Windows socket issues
        print("ERROR: Failed to bind socket.")
        print(f"  host={host} port={port}")
        print(f"  reload={reload_flag} reload_dirs={reload_dirs} reload_excludes={reload_excludes}")
        print(f"  PYTHONPATH={os.environ.get('PYTHONPATH')}")
        print(
            "Possible causes: port already in use, OS reserved port range, firewall/antivirus or insufficient privileges."
        )
        print("Useful checks (PowerShell):")
        print("  netstat -ano | findstr :<PORT>")
        print("  netsh interface ipv4 show excludedportrange protocol=tcp")
        print("  Run PowerShell as Administrator and retry, or try a different port (>=1025)")
        raise


if __name__ == "__main__":
    run()
