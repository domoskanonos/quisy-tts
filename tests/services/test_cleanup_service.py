from infrastructure.cleanup_service import FileCleanupService
from pathlib import Path
import os
import time


def test_cleanup_service(tmp_path):
    # Setup
    cleanup = FileCleanupService()

    # Create test files
    dir = tmp_path / "audio"
    dir.mkdir()

    old_file = dir / "old.wav"
    old_file.write_text("old")
    # Set mtime to 48 hours ago
    old_time = time.time() - (48 * 3600)
    os.utime(old_file, (old_time, old_time))

    new_file = dir / "new.wav"
    new_file.write_text("new")

    cache_file = dir / "cache_123.wav"
    cache_file.write_text("cache")

    # Run
    removed = cleanup.cleanup_old_files(dir, max_age_hours=24)

    # Assert
    assert removed == 1
    assert not old_file.exists()
    assert new_file.exists()
    assert cache_file.exists()


def test_cleanup_service_no_dir():
    cleanup = FileCleanupService()
    removed = cleanup.cleanup_old_files(Path("nonexistent"), max_age_hours=24)
    assert removed == 0
