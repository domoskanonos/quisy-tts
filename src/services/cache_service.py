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
        """Generate a stable cache key from text and parameters.

        The key includes a normalized form of the text and all generation parameters
        that can influence the produced audio (language, mode, model size, reference
        audio, ref_text, instruct and speaker). The normalization trims and
        collapses whitespace so minor formatting changes don't cause cache misses.

        We use SHA-256 to avoid MD5 collisions and produce a compact hex digest.
        """
        # Normalize text: trim and collapse all whitespace to a single space
        normalized_text = " ".join(text.split()) if text is not None else ""

        # Include all parameters that affect the output audio in the hash
        parts = [
            normalized_text,
            params.language or "",
            params.mode or "",
            params.model_size or "",
            params.reference_audio or "",
            params.ref_text or "",
            params.instruct or "",
            params.speaker or "",
        ]

        content = ":".join(parts)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

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
