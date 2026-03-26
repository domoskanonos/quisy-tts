import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

import asyncio

from engine.qwen import QwenTextToSpeech
from schemas import TTSParams


async def benchmark() -> None:
    print("Initializing Engine...")
    engine = QwenTextToSpeech()

    params = TTSParams(language="German", mode="base", model_size="0.6B")

    text = "Dies ist ein deutlich längerer Text, um das Streaming besser zu testen."

    print(f"Generating for text ({len(text)} chars): '{text}'")

    # Warmup
    # print("Warming up...")
    # await engine.generate_audio("Hallo", params)

    start = time.time()
    waveform, sr = await engine.generate_audio(text, params)
    duration = time.time() - start

    print(f"Generation took: {duration:.4f}s")
    print(f"RTF: {duration / (waveform.shape[1] / sr):.4f}")

    # Check device again from within the engine if possible, or assume logs printed it


if __name__ == "__main__":
    asyncio.run(benchmark())
