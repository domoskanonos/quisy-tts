import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from services import FileCacheService
from services.tts_service import TTSService

# Use a lightweight dummy engine in tests to avoid heavy qwen model loading
from unittest.mock import AsyncMock
from schemas import TTSParams


class DummyEngine:
    def __init__(self):
        self.generate_and_save = AsyncMock(side_effect=self._gen)

    async def _gen(self, text, output_path, params):
        # Simulate some async work and write a small wav-ish file
        await asyncio.sleep(0.01)
        # write a tiny valid WAV file using soundfile
        import numpy as np
        import soundfile as sf

        sr = 24000
        t = np.linspace(0, 0.01, int(sr * 0.01), endpoint=False)
        data = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(p), data, sr)
        return str(p)


@pytest.mark.asyncio
async def test_concurrent_same_text_generates_once(tmp_path):
    """Simulate multiple concurrent requests for the same long text.

    The engine's underlying generate_and_save should be invoked only once per
    chunk; subsequent coroutines should reuse the cache.
    """
    # Use file-based cache in tmp dir
    cache = FileCacheService(cache_dir=tmp_path)
    engine = DummyEngine()
    service = TTSService(engine, cache)

    long_text = "Dies ist ein sehr langer Text. " * 20

    params = TTSParams(language="german", mode="voice_design", model_size="1.7b")

    # Run multiple concurrent generation tasks
    async def call_gen():
        path = await service.generate_audio(long_text, params.language, params.mode, params.model_size)
        return path

    # Run 3 concurrent calls
    tasks = [asyncio.create_task(call_gen()) for _ in range(3)]
    results = await asyncio.gather(*tasks)

    # All tasks should return a Path (string-like) and be equal (same cached file)
    assert all(str(results[0]) == str(r) for r in results)
