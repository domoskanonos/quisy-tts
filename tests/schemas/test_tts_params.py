"""Tests for TTSParams schema."""

import pytest

from schemas.internal import TTSParams


class TestTTSParams:
    def test_default_values(self) -> None:
        params = TTSParams()
        assert params.mode == "base"
        assert params.model_size == "1.7B"
        assert params.language is None
        assert params.reference_audio is None
        assert params.ref_text is None
        assert params.instruct is None
        assert params.speaker is None
        assert params.ref_audio_path is None

    def test_custom_values(self) -> None:
        params = TTSParams(
            language="german",
            mode="voice_design",
            model_size="0.6B",
            instruct="A calm voice",
            ref_audio_path="/tmp/audio.wav",
        )
        assert params.language == "german"
        assert params.mode == "voice_design"
        assert params.model_size == "0.6B"
        assert params.instruct == "A calm voice"
        assert params.ref_audio_path == "/tmp/audio.wav"

    def test_resolved_language_raises_when_unset(self) -> None:
        params = TTSParams()
        with pytest.raises(ValueError, match="language is not set"):
            _ = params.resolved_language

    def test_resolved_language_returns_full_name(self) -> None:
        params = TTSParams(language="german")
        assert params.resolved_language == "german"
