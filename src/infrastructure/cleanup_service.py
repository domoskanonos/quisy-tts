"""File cleanup service implementation."""

import time
from pathlib import Path

from config import ProjectConfig
from core import CleanupService


logger = ProjectConfig.get_logger()


class FileCleanupService(CleanupService):
    """File-based implementation of CleanupService."""

    def cleanup_old_files(self, directory: Path, max_age_hours: int = 24) -> int:
        """Remove files older than max_age_hours from directory.

        Args:
            directory: Directory to clean.
            max_age_hours: Maximum age of files to keep.

        Returns:
            Number of files removed.
        """
        if not directory.exists():
            return 0

        cutoff = time.time() - (max_age_hours * 3600)
        cleaned = 0

        for file in directory.glob("*.wav"):
            # Don't delete cache files
            if file.name.startswith("cache_"):
                continue
            if file.stat().st_mtime < cutoff:
                file.unlink()
                cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old audio files from {directory}")

        return cleaned
