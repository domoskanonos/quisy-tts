#!/usr/bin/env python3
# Small demo script to exercise TTSService with a DummyEngine and show cache logs.
import asyncio
from pathlib import Path
import sys

# Ensure src is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from services.cache_service import FileCacheService
from services.tts_service import TTSService


class DummyEngine:
    async def generate_and_save(self, text, output_path, params):
        # Lightweight generator that writes a tiny WAV using soundfile
        import numpy as np
        import soundfile as sf

        sr = 24000
        t = np.linspace(0, 0.01, int(sr * 0.01), endpoint=False)
        data = 0.05 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(p), data, sr)
        return str(p)


async def main():
    cache = FileCacheService(cache_dir=Path("output_demo"))
    engine = DummyEngine()
    service = TTSService(engine, cache)

    text = "Dies ist ein Beispieltext zum Testen des Caches."
    # First call: should generate
    print("First generation (should generate):")
    p1 = await service.generate_audio(text, "german", "voice_design", "1.7B")
    print("->", p1)

    # Second call: should hit cache
    print("Second generation (should hit cache):")
    p2 = await service.generate_audio(text, "german", "voice_design", "1.7B")
    print("->", p2)


if __name__ == "__main__":
    asyncio.run(main())
