from pathlib import Path
from config import ProjectConfig
from core import AudioGenerationError
from schemas import TTSParams
from schemas.languages import resolve_language
from services.voice_service import VoiceService


async def generate_audio(
    service,
    text: str,
    language: str,
    mode: str,
    model_size: str,
    reference_audio: str | None = None,
    ref_text: str | None = None,
    instruct: str | None = None,
    speaker: str | None = None,
) -> Path:
    """Generate audio from text with caching and smart splitting."""
    resolved = resolve_language(language)
    final_instruct = instruct
    try:
        if final_instruct and resolved == "german":
            low = final_instruct.lower()
            if not ("sprich" in low or "auf deutsch" in low or "in german" in low):
                final_instruct = "Sprich auf Deutsch. " + final_instruct
    except Exception:
        final_instruct = instruct

    if not ref_text and reference_audio:
        vs = VoiceService()
        voice = vs.get_voice(reference_audio)
        if voice:
            ref_text = voice.get("example_text")
            await service._ensure_reference_audio(reference_audio)

    params = TTSParams(
        language=resolved,
        reference_audio=reference_audio,
        ref_text=ref_text,
        mode=mode,
        model_size=model_size,
        instruct=final_instruct,
        speaker=speaker,
    )

    global_key = service.cache.get_key(text, params)
    if cached_path := service.cache.get(global_key):
        return cached_path

    chunks = service.text_splitter.split(text, params.language or "german")
    if not chunks:
        raise AudioGenerationError("Text is empty after splitting")

    chunk_paths: list[Path] = []
    for i, chunk_text in enumerate(chunks):
        chunk_key = service.cache.get_key(chunk_text, params)
        if chunk_path := service.cache.get(chunk_key):
            chunk_paths.append(chunk_path)
            continue

        lock = service._get_lock(chunk_key)
        async with lock:
            if chunk_path := service.cache.get(chunk_key):
                chunk_paths.append(chunk_path)
            else:
                output_path = ProjectConfig.get_settings().OUTPUT_DIR / f"cache_{chunk_key}.wav"
                try:
                    result_path = await service.engine.generate_and_save(chunk_text, str(output_path), params)
                    chunk_path = Path(result_path)
                    service.cache.set(chunk_key, chunk_path)
                    chunk_paths.append(chunk_path)
                except Exception as e:
                    raise AudioGenerationError(f"Chunk generation failed: {e}") from e

    # ... (Concatenation logic remains here in generator for now to be moved if needed)
    return chunk_paths[0]
