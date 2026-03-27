"""File-based cache service implementation."""

import hashlib
import time
import shutil
from pathlib import Path

from config import ProjectConfig
from core import CacheService
from schemas import TTSParams
import asyncio
import weakref

logger = ProjectConfig.get_logger()


class FileCacheService(CacheService):
    """File-based implementation of CacheService."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the file cache service.

        Args:
            cache_dir: Directory to store cached files. Defaults to OUTPUT_DIR.
        """
        self.cache_dir = cache_dir or ProjectConfig.get_settings().OUTPUT_DIR
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

    def cleanup_old_files(self, directory: Path | None = None, max_age_hours: int = 24 * 30) -> int:
        """Remove files older than `max_age_hours` from the cache directory.

        Args:
            directory: Optional directory to clean. Defaults to the configured cache dir.
            max_age_hours: Files older than this (hours) will be removed. Default is 30 days.

        Returns:
            Number of files removed.
        """
        target_dir = directory or self.cache_dir
        if not target_dir.exists():
            logger.info(f"Cache cleanup: directory does not exist: {target_dir}")
            return 0

        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0

        for p in target_dir.iterdir():
            try:
                if not p.is_file():
                    continue
                # Only act on cache files by convention (prefix), but be conservative
                if not p.name.startswith("cache_"):
                    continue

                mtime = p.stat().st_mtime
                if mtime < cutoff:
                    p.unlink()
                    removed += 1
                    logger.info(f"Cache cleanup: removed old file {p.name}")
            except Exception as e:
                logger.warning(f"Cache cleanup: failed to remove {p}: {e}")
        logger.info(f"Cache cleanup: removed {removed} files from {target_dir}")
        return removed
