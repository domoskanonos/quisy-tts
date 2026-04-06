"""SSML (Speech Synthesis Markup Language) processing service.

Provides functionality to parse SSML and orchestrate audio generation tasks
for multiple text chunks and silences.
"""

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from config import ProjectConfig
from core import AudioGenerationError
from schemas.languages import resolve_language
from services.ssml_processor import BreakTask, TextTask


async def _ensure_speakers_integrity(service: Any, tasks: list[Any]) -> None:
    """Ensures all speakers in text tasks have valid audio integrity.

    Args:
        service: The TTS service instance providing access to voice and audio services.
        tasks: A list of processing tasks (TextTask or BreakTask).

    Raises:
        AudioGenerationError: If a speaker ID is not found or audio integrity check fails.
    """
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


async def _process_task(
    service: Any, task: Any, i: int, total_tasks: int, sample_rate: int, base_params: Any
) -> tuple[np.ndarray | None, int]:
    """Processes a single SSML task (text or break).

    Args:
        service: The TTS service instance.
        task: The task to process (TextTask or BreakTask).
        i: Current task index.
        total_tasks: Total number of tasks.
        sample_rate: Current audio sample rate.
        base_params: Base generation parameters.

    Returns:
        A tuple containing the generated audio waveform (numpy array) and the sample rate.
        Returns (None, sample_rate) for non-audio producing tasks or if generation failed.
    """
    if isinstance(task, TextTask):
        service.logger.info(f"SSML: Processing text task {i + 1}/{total_tasks} (speaker={task.speaker})")
        voice = service.voice_service.get_voice(task.speaker)
        if not voice:
            raise AudioGenerationError(f"Speaker ID {task.speaker} not found")

        lang = voice.get("language")
        if not lang:
            raise AudioGenerationError(f"Voice '{voice['voice_id']}' has no language set")

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
        return data, sr
    elif isinstance(task, BreakTask):
        service.logger.info(f"SSML: Processing break task {i + 1} ({task.duration_ms}ms)")
        silence_samples = int(sample_rate * (task.duration_ms / 1000))
        return np.zeros(silence_samples, dtype=np.float32), sample_rate
    return None, sample_rate


async def generate_from_ssml(service: Any, ssml_content: str, base_params: Any) -> Path:
    """Parses SSML content, orchestrates audio generation for all tasks, and saves the final audio.

    Args:
        service: The TTS service instance.
        ssml_content: The SSML string to be processed.
        base_params: Base generation parameters.

    Returns:
        Path to the final generated audio file.

    Raises:
        AudioGenerationError: If speaker integrity or audio generation fails.
    """
    tasks = service.ssml_processor.parse(ssml_content)
    combined_audio = []
    sample_rate = 24000

    await _ensure_speakers_integrity(service, tasks)

    for i, task in enumerate(tasks):
        data, new_sr = await _process_task(service, task, i, len(tasks), sample_rate, base_params)
        if data is not None:
            combined_audio.append(data)
            sample_rate = new_sr

    final_audio = np.concatenate(combined_audio)
    ssml_key = hashlib.sha256(ssml_content.encode()).hexdigest()[:12]
    output_path = ProjectConfig.get_settings().AUDIO_DIR / f"ssml_{ssml_key}.wav"
    sf.write(str(output_path), final_audio, sample_rate)
    return output_path
