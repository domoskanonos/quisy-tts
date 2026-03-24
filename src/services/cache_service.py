"""File-based cache service implementation."""

import hashlib
import shutil
from pathlib import Path

from config import ProjectConfig
from core import CacheService
from schemas import TTSParams
import asyncio
import weakref

logger = ProjectConfig.get_logger()
settings = ProjectConfig.get_settings()


class FileCacheService(CacheService):
    """File-based implementation of CacheService."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the file cache service.

        Args:
            cache_dir: Directory to store cached files. Defaults to OUTPUT_DIR.
        """
        self.cache_dir = cache_dir or settings.OUTPUT_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # locks per cache key to avoid duplicate generation across processes
        # Use a WeakValueDictionary so locks can be GC'd when no longer referenced.
        self._locks: "weakref.WeakValueDictionary[str, asyncio.Lock]" = weakref.WeakValueDictionary()

    def get_lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            try:
                self._locks[key] = lock
            except Exception:
                # WeakValueDictionary may raise if key isn't hashable; fall back silently
                pass
        return lock

    def get_key(self, text: str, params: TTSParams) -> str:
        """Generate a cache key from text and parameters."""
        # Include all parameters that affect the output audio in the hash
        content = (
            f"{text}:"
            f"{params.language}:"
            f"{params.mode}:"
            f"{params.model_size}:"
            f"{params.reference_audio or ''}:"
            f"{params.ref_text or ''}:"
            f"{params.instruct or ''}:"
            f"{params.speaker or ''}"
        )
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> Path | None:
        """Retrieve cached audio by key."""
        cache_path = self.cache_dir / f"cache_{key}.wav"
        if cache_path.exists():
            logger.info(f"Cache hit for key: {key[:8]}...")
            return cache_path
        return None

    def set(self, key: str, path: Path) -> None:
        """Store audio in cache by copying to cache location."""
        cache_path = self.cache_dir / f"cache_{key}.wav"
        if path != cache_path and path.exists():
            shutil.copy2(path, cache_path)
            logger.info(f"Cached audio with key: {key[:8]}...")
