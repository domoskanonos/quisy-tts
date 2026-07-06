"""Tests for FileCacheService."""

from pathlib import Path

import pytest

from infrastructure.cache_service import FileCacheService
from schemas.internal import TTSParams


@pytest.fixture
def cache(tmp_path: Path) -> FileCacheService:
    return FileCacheService(tmp_path / "cache")


class TestFileCacheService:
    def test_get_key_deterministic(self, cache: FileCacheService) -> None:
        params = TTSParams(mode="base", language="german")
        key1 = cache.get_key("Hello", params)
        key2 = cache.get_key("Hello", params)
        assert key1 == key2

    def test_get_key_different_text(self, cache: FileCacheService) -> None:
        params = TTSParams(mode="base", language="german")
        assert cache.get_key("Hello", params) != cache.get_key("World", params)

    def test_get_key_different_params(self, cache: FileCacheService) -> None:
        p1 = TTSParams(mode="base", language="german")
        p2 = TTSParams(mode="base", language="english")
        assert cache.get_key("Hello", p1) != cache.get_key("Hello", p2)

    def test_get_key_whitespace_normalization(self, cache: FileCacheService) -> None:
        params = TTSParams(mode="base", language="german")
        assert cache.get_key("  Hello   World  ", params) == cache.get_key("Hello World", params)

    def test_set_and_get(self, cache: FileCacheService, tmp_path: Path) -> None:
        params = TTSParams(mode="base", language="german")
        key = cache.get_key("test", params)
        audio_file = tmp_path / "source.wav"
        audio_file.write_bytes(b"audio data")
        cache.set(key, audio_file)
        cached = cache.get(key)
        assert cached is not None
        assert cached.read_bytes() == b"audio data"

    def test_get_nonexistent_returns_none(self, cache: FileCacheService) -> None:
        assert cache.get("nonexistent_key") is None

    def test_get_lock_returns_same_instance(self, cache: FileCacheService) -> None:
        import asyncio

        lock1 = cache.get_lock("test_key")
        lock2 = cache.get_lock("test_key")
        assert lock1 is lock2
        assert isinstance(lock1, asyncio.Lock)

    def test_cleanup_old_files(self, cache: FileCacheService, tmp_path: Path) -> None:
        import os
        import time

        old_file = cache.cache_dir / "cache_old.wav"
        old_file.write_bytes(b"old")
        old_time = time.time() - (48 * 3600)
        os.utime(old_file, (old_time, old_time))

        new_file = cache.cache_dir / "cache_new.wav"
        new_file.write_bytes(b"new")

        removed = cache.cleanup_old_files(max_age_hours=24)
        assert removed == 1
        assert not old_file.exists()
        assert new_file.exists()
