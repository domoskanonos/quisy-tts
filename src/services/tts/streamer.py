import numpy as np
import soundfile as sf
from pathlib import Path
from collections.abc import AsyncGenerator
from config import ProjectConfig
from core import AudioGenerationError
from schemas import TTSParams
from schemas.languages import resolve_language


async def generate_stream(
    service,
    text: str,
    language: str,
    mode: str,
    model_size: str,
    reference_audio: str | None = None,
    ref_text: str | None = None,
    instruct: str | None = None,
    speaker: str | None = None,
    chunk_size: int = 4096,
) -> AsyncGenerator[bytes, None]:
    """Generate audio stream from text with caching."""
    params = TTSParams(
        language=resolve_language(language),
        reference_audio=reference_audio,
        ref_text=ref_text,
        mode=mode,
        model_size=model_size,
        instruct=instruct,
        speaker=speaker,
    )

    global_key = service.cache.get_key(text, params)

    # Check global cache first
    if cached_path := service.cache.get(global_key):
        with sf.SoundFile(str(cached_path)) as f:
            while True:
                data = f.read(dtype="int16", frames=chunk_size // 2)
                if len(data) == 0:
                    break
                yield data.tobytes()
        return

    # Process chunks
    chunks = service.text_splitter.split(text, params.language or "german")
    for i, chunk_text in enumerate(chunks):
        chunk_key = service.cache.get_key(chunk_text, params)
        chunk_path = service.cache.get(chunk_key)
        if not chunk_path:
            lock = service._get_lock(chunk_key)
            async with lock:
                chunk_path = service.cache.get(chunk_key)
                if not chunk_path:
                    output_path = ProjectConfig.get_settings().OUTPUT_DIR / f"cache_{chunk_key}.wav"
                    try:
                        result_path = await service.engine.generate_and_save(chunk_text, str(output_path), params)
                        chunk_path = Path(result_path)
                        service.cache.set(chunk_key, chunk_path)
                    except Exception as e:
                        raise AudioGenerationError(f"Stream generation failed: {e}") from e

        # Stream chunk
        with sf.SoundFile(str(chunk_path)) as f:
            while True:
                data = f.read(dtype="int16", frames=chunk_size // 2)
                if len(data) == 0:
                    break
                yield data.tobytes()

        # Yield silence
        if i < len(chunks) - 1:
            try:
                sr = sf.info(str(chunk_path)).samplerate
                yield np.zeros(int(sr * 0.15), dtype=np.int16).tobytes()
            except Exception:
                pass
