from pathlib import Path

from infrastructure.cache_service import FileCacheService
from schemas import TTSParams


def test_cache_persistence():
    cache = FileCacheService(Path("test_cache"))
    params = TTSParams(mode="base", language="german")
    text = "Hallo"
    key = cache.get_key(text, params)

    # Simulate a file content
    content = b"fake_wav_data"
    temp_file = Path("temp_audio.wav")
    temp_file.write_bytes(content)

    cache.set(key, temp_file)
    cached_path = cache.get(key)

    assert cached_path is not None
    assert cached_path.read_bytes() == content

    # Clean up
    temp_file.unlink()
    if cached_path.exists():
        cached_path.unlink()
    Path("test_cache").rmdir()
