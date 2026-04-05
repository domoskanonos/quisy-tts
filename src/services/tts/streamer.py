import numpy as np
import soundfile as sf
from collections.abc import AsyncGenerator
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
        reference_audio_path=service.voice_service.resolve_reference_audio(reference_audio),
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
    if not params.language:
        raise AudioGenerationError("language is required for streaming generation")

    chunks = service.text_splitter.split(text, params.language)
    for i, chunk_text in enumerate(chunks):
        chunk_key = service.cache.get_key(chunk_text, params)
        chunk_path = service.cache.get(chunk_key)
        if not chunk_path:
            lock = service._get_lock(chunk_key)
            async with lock:
                chunk_path = service.cache.get(chunk_key)
                if not chunk_path:
                    try:
                        audio_bytes, sr = await service.engine.generate_audio_bytes(chunk_text, params)
                        # Yield the actual bytes first to minimize latency
                        for k in range(0, len(audio_bytes), chunk_size):
                            yield audio_bytes[k : k + chunk_size]

                        # Cache asynchronously in background
                        service.cache.set_bytes(chunk_key, audio_bytes)
                    except Exception as e:
                        raise AudioGenerationError(f"Stream generation failed: {e}") from e

        else:
            # Stream chunk from disk cache
            with sf.SoundFile(str(chunk_path)) as f:
                while True:
                    data = f.read(dtype="int16", frames=chunk_size // 2)
                    if len(data) == 0:
                        break
                    yield data.tobytes()

        # Yield silence
        if i < len(chunks) - 1:
            try:
                # Assuming standard 24kHz if we just generated, otherwise check info
                sr = 24000
                if chunk_path:
                    sr = sf.info(str(chunk_path)).samplerate
                yield np.zeros(int(sr * 0.15), dtype=np.int16).tobytes()
            except Exception:
                pass
