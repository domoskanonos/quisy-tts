import pytest
from services.text_splitter import get_text_splitter
from services.cache_service import FileCacheService
from schemas import TTSParams
from pathlib import Path
import numpy as np


def test_spacy_splitting():
    text = "Dies ist Satz 1. Dies ist Satz 2. Dies ist Satz 3."
    splitter = get_text_splitter(max_chunk_chars=10)  # Small limit to force split
    chunks = splitter.split(text, language="german")

    assert len(chunks) > 1
    # Ensure no sentence is lost
    full_text = " ".join(chunks)
    assert len(full_text.split()) == len(text.split())


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
