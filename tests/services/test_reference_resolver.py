"""Tests for reference audio path resolution."""

from pathlib import Path

import pytest

from core.exceptions import ReferenceAudioNotFoundError
from services.orchestrator.reference_resolver import require_ref_audio_path, resolve_ref_audio_path


def _get_filename(voice_id: str) -> str:
    return f"voice_{voice_id}.wav"


@pytest.fixture
def voices_dir(tmp_path: Path) -> Path:
    d = tmp_path / "voices"
    d.mkdir()
    (d / "voice_existing.wav").write_bytes(b"fake audio")
    return d


class TestResolveRefAudioPath:
    def test_finds_existing_voice(self, voices_dir: Path) -> None:
        result = resolve_ref_audio_path("existing", voices_dir, _get_filename)
        assert result is not None
        assert result.endswith("voice_existing.wav")

    def test_falls_back_to_default_voice(self, voices_dir: Path) -> None:
        (voices_dir / "voice_default.wav").write_bytes(b"default audio")
        result = resolve_ref_audio_path("nonexistent", voices_dir, _get_filename, default_voice_id="default")
        assert result is not None
        assert result.endswith("voice_default.wav")

    def test_falls_back_to_first_wav(self, voices_dir: Path) -> None:
        result = resolve_ref_audio_path("nonexistent", voices_dir, _get_filename)
        assert result is not None
        assert result.endswith(".wav")

    def test_returns_none_when_no_audio(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = resolve_ref_audio_path("test", empty_dir, _get_filename)
        assert result is None


class TestRequireRefAudioPath:
    def test_raises_when_not_found(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(ReferenceAudioNotFoundError):
            require_ref_audio_path("test", empty_dir, _get_filename)

    def test_returns_path_when_found(self, voices_dir: Path) -> None:
        result = require_ref_audio_path("existing", voices_dir, _get_filename)
        assert result.endswith("voice_existing.wav")
