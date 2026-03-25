"""CLI helper to run the app in development mode with hot reload.

This provides a simple entrypoint that reads UV_HOST/UV_PORT and starts
uvicorn with reload enabled so code changes are picked up automatically.
"""

from __future__ import annotations

import os
import typing

import uvicorn

from api import app


def _get_env(name: str, default: typing.Any) -> typing.Any:
    val = os.environ.get(name)
    if val is None:
        return default
    return val


def run() -> None:
    host = _get_env("UV_HOST", "127.0.0.1")
    port = int(_get_env("UV_PORT", "8000"))
    # Enable reload for development
    uvicorn.run(app, host=host, port=port, reload=True)


if __name__ == "__main__":
    run()
