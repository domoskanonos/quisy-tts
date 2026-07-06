"""Reference audio resolution helper – lives in the application layer."""

from __future__ import annotations

from pathlib import Path

from core.exceptions import ReferenceAudioNotFoundError


def resolve_ref_audio_path(
    reference_audio: str | None,
    voices_dir: Path,
    get_filename_fn,
    default_voice_id: str | None = None,
) -> str | None:
    """Resolve a voice ID to a physical audio file path.

    Args:
        reference_audio: The voice ID requested by the caller.
        voices_dir: Directory where voice audio files are stored.
        get_filename_fn: Callable that maps voice_id -> filename.
        default_voice_id: Optional fallback voice ID from settings.

    Returns:
        Absolute path string to the audio file, or None if not found.
    """
    if reference_audio:
        path = voices_dir / get_filename_fn(reference_audio)
        if path.exists():
            return str(path)

    if default_voice_id:
        path = voices_dir / get_filename_fn(default_voice_id)
        if path.exists():
            return str(path)

    voices = list(voices_dir.glob("*.wav"))
    return str(voices[0]) if voices else None


def require_ref_audio_path(
    reference_audio: str | None,
    voices_dir: Path,
    get_filename_fn,
    default_voice_id: str | None = None,
) -> str:
    """Like resolve_ref_audio_path but raises if no audio is found."""
    path = resolve_ref_audio_path(reference_audio, voices_dir, get_filename_fn, default_voice_id)
    if not path:
        raise ReferenceAudioNotFoundError("No reference audio found.")
    return path
