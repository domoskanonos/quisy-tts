from audio.processor import AudioProcessor
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
    skip_integrity_check: bool = False,
) -> Path:
    """Generate audio from text with caching and smart splitting."""
    voice_or_speaker = reference_audio or speaker or "default"
    service.logger.info(f"Generating with voice: {voice_or_speaker}")
    service.logger.info(f"Text: {text}")

    resolved = resolve_language(language)
    final_instruct = instruct

    if not skip_integrity_check and not ref_text and reference_audio:
        vs = VoiceService()
        voice = vs.get_voice(reference_audio)
        if voice:
            ref_text = voice.get("example_text")
            await service.voice_audio_integrity.ensure_audio(reference_audio)

    # Validate that instruction text is provided when reference audio (voice cloning) is used
    if reference_audio and not instruct:
        raise AudioGenerationError("Instruction text is required when using reference audio for voice cloning.")

    # Log voice cloning attempt
    if reference_audio and instruct:
        service.logger.info(f"Voice cloning with instruct text and voice: ID={reference_audio}, Instruct='{instruct}'")

    params = TTSParams(
        language=resolved,
        reference_audio=reference_audio,
        reference_audio_path=service.voice_service.resolve_reference_audio(reference_audio),
        ref_text=ref_text,
        mode=mode,
        model_size=model_size,
        instruct=final_instruct,
        speaker=speaker,
    )

    global_key = service.cache.get_key(text, params)
    if cached_path := service.cache.get(global_key):
        return cached_path

    # language must be provided by the caller (API layer). Use the resolved
    # language from params directly when splitting text.
    chunks = service.text_splitter.split(text, params.language)
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
                output_path = ProjectConfig.get_settings().AUDIO_DIR / f"cache_{chunk_key}.wav"
                try:
                    result_path = await service.engine.generate_and_save(chunk_text, str(output_path), params)
                    chunk_path = Path(result_path)
                    service.cache.set(chunk_key, chunk_path)
                    chunk_paths.append(chunk_path)
                except Exception as e:
                    raise AudioGenerationError(f"Chunk generation failed: {e}") from e

    if len(chunk_paths) > 1:
        combined_output_path = ProjectConfig.get_settings().AUDIO_DIR / f"cache_{global_key}.wav"
        if not combined_output_path.exists():
            if not AudioProcessor.concatenate_audio([str(p) for p in chunk_paths], str(combined_output_path)):
                raise AudioGenerationError("Concatenation failed")
            service.cache.set(global_key, combined_output_path)
        return combined_output_path

    return chunk_paths[0]
