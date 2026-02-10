"""File-based cache service implementation."""

import hashlib
import shutil
from pathlib import Path

from config import ProjectConfig
from core import CacheService
from schemas import TTSParams


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

    def get_key(self, text: str, params: TTSParams) -> str:
        """Generate a cache key from text and parameters."""
        content = f"{text}:{params.language}:{params.mode}:{params.model_size}"
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
