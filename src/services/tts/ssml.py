from pathlib import Path
from config import ProjectConfig
from core import AudioGenerationError
from services.ssml_processor import TextTask, BreakTask
import hashlib
import numpy as np
import soundfile as sf


async def generate_from_ssml(service, ssml_content: str, base_params) -> Path:
    """Generate audio from SSML content."""
    tasks = service.ssml_processor.parse(ssml_content)
    combined_audio = []
    sample_rate = 24000

    # Ensure integrity check...
    unique_speakers = {task.speaker for task in tasks if isinstance(task, TextTask)}
    for speaker in unique_speakers:
        voice = service.voice_service.get_voice(speaker)
        if not voice:
            raise AudioGenerationError(f"Speaker ID {speaker} not found")
        service.logger.info(f"SSML: Checking integrity for {voice['voice_id']}")
        try:
            await service.voice_audio_integrity.ensure_audio(voice["voice_id"], service.generate_audio)
        except Exception as e:
            service.logger.error(f"SSML: Integrity check FAILED for {voice['voice_id']}: {e}")
            raise

    for i, task in enumerate(tasks):
        if isinstance(task, TextTask):
            service.logger.info(f"SSML: Processing text task {i + 1}/{len(tasks)} (speaker={task.speaker})")
            voice = service.voice_service.get_voice(task.speaker)
            if not voice:
                raise AudioGenerationError(f"Speaker ID {task.speaker} not found")

            # Ensure the voice entry has the language field — it must exist.
            lang = voice.get("language")
            if not lang:
                raise AudioGenerationError(f"Voice '{voice['voice_id']}' has no language set")

            # Ensure language is resolved correctly
            from schemas.languages import resolve_language

            resolved_lang = resolve_language(lang)

            chunk_path = await service.generate_audio(
                task.text,
                resolved_lang,
                "base",
                base_params.model_size or "1.7B",
                reference_audio=voice["voice_id"],
                ref_text=voice.get("example_text"),
                instruct=voice.get("instruct"),
                speaker=voice["voice_id"],
            )
            service.logger.info(f"SSML: Chunk {i + 1} generated at {chunk_path}")

            data, sr = sf.read(str(chunk_path))
            combined_audio.append(data)
            sample_rate = sr
        elif isinstance(task, BreakTask):
            service.logger.info(f"SSML: Processing break task {i + 1} ({task.duration_ms}ms)")
            silence_samples = int(sample_rate * (task.duration_ms / 1000))
            combined_audio.append(np.zeros(silence_samples, dtype=np.float32))

    final_audio = np.concatenate(combined_audio)
    ssml_key = hashlib.sha256(ssml_content.encode()).hexdigest()[:12]
    output_path = ProjectConfig.get_settings().AUDIO_DIR / f"ssml_{ssml_key}.wav"
    sf.write(str(output_path), final_audio, sample_rate)
    return output_path
