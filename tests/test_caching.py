import pytest
from pathlib import Path
from services.tts_service import TTSService
from schemas import TTSParams
import shutil

# This would need a running engine or mock, but let's test the CacheService directly
from services.cache_service import FileCacheService


def test_cache_service():
    cache = FileCacheService(Path("test_cache"))
    params = TTSParams(mode="base", language="german")
    key = cache.get_key("Hallo", params)

    # Create a dummy file
    dummy_file = Path("dummy.wav")
    dummy_file.write_text("audio_data")

    # Set and get
    cache.set(key, dummy_file)
    cached_path = cache.get(key)

    assert cached_path is not None
    assert cached_path.exists()
    assert cached_path.read_text() == "audio_data"

    # Clean up
    dummy_file.unlink()
    shutil.rmtree(Path("test_cache"))
