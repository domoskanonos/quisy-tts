from pathlib import Path

from audio.processor import AudioProcessor
from config import ProjectConfig
from core import AudioGenerationError
from schemas import TTSParams
from schemas.languages import resolve_language
from services.orchestrator.reference_resolver import resolve_ref_audio_path
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
    """Generate audio from text with caching."""
    voice_or_speaker = reference_audio or speaker or "default"
    service.logger.info(f"Generating with voice: {voice_or_speaker}")
    service.logger.info(f"Text: {text}")

    resolved = resolve_language(language)
    final_instruct = instruct

    settings = ProjectConfig.get_settings()

    if not skip_integrity_check and not ref_text and reference_audio:
        vs = VoiceService()
        voice = vs.get_voice(reference_audio)
        if voice:
            ref_text = voice.get("example_text")
            await service.voice_audio_integrity.ensure_audio(reference_audio)

    if reference_audio and not instruct:
        raise AudioGenerationError("Instruction text is required when using reference audio for voice cloning.")

    if reference_audio and instruct:
        service.logger.info(f"Voice cloning with instruct text and voice: ID={reference_audio}, Instruct='{instruct}'")

    ref_audio_path = None
    if mode != "voice_design":
        ref_audio_path = resolve_ref_audio_path(
            reference_audio=reference_audio,
            voices_dir=settings.VOICES_DIR,
            get_filename_fn=service.voice_service.get_voice_filename
            if hasattr(service.voice_service, "get_voice_filename")
            else lambda vid: f"voice_{vid}.wav",
            default_voice_id=settings.DEFAULT_VOICE_ID,
        )

    params = TTSParams(
        language=resolved,
        reference_audio=reference_audio,
        ref_text=ref_text,
        mode=mode,
        model_size=model_size,
        instruct=final_instruct,
        speaker=speaker,
        ref_audio_path=ref_audio_path,
    )

    global_key = service.cache.get_key(text, params)
    if cached_path := service.cache.get(global_key):
        return cached_path

    chunks = [text]
    if not chunks[0].strip():
        raise AudioGenerationError("Text is empty after trimming")

    chunk_paths: list[Path] = []
    for chunk_text in chunks:
        chunk_key = service.cache.get_key(chunk_text, params)
        if chunk_path := service.cache.get(chunk_key):
            chunk_paths.append(chunk_path)
            continue

        lock = service._get_lock(chunk_key)
        async with lock:
            if chunk_path := service.cache.get(chunk_key):
                chunk_paths.append(chunk_path)
            else:
                output_path = settings.AUDIO_DIR / f"cache_{chunk_key}.wav"
                try:
                    result_path = await service.engine.generate_and_save(chunk_text, str(output_path), params)
                    chunk_path = Path(result_path)
                    service.cache.set(chunk_key, chunk_path)
                    chunk_paths.append(chunk_path)
                except Exception as e:
                    raise AudioGenerationError(f"Chunk generation failed: {e}") from e

    if len(chunk_paths) > 1:
        combined_output_path = settings.AUDIO_DIR / f"cache_{global_key}.wav"
        if not combined_output_path.exists():
            if not AudioProcessor.concatenate_audio([str(p) for p in chunk_paths], str(combined_output_path)):
                raise AudioGenerationError("Concatenation failed")
            service.cache.set(global_key, combined_output_path)
        return combined_output_path

    return chunk_paths[0]
