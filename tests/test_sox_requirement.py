import pytest
import shutil
from unittest.mock import patch, MagicMock
from src.audio.processor import SoxAudioProcessor, SoxNotFoundError
from src.services.tts_service import TTSService


def test_sox_check_availability_success():
    """Test that check_availability succeeds when sox is found."""
    with patch("shutil.which", return_value="/usr/bin/sox"):
        SoxAudioProcessor._is_available = None  # Reset state
        SoxAudioProcessor.check_availability()
        assert SoxAudioProcessor._is_available is True


def test_sox_check_availability_failure():
    """Test that check_availability raises SoxNotFoundError when sox is missing."""
    with patch("shutil.which", return_value=None):
        SoxAudioProcessor._is_available = None  # Reset state
        with pytest.raises(SoxNotFoundError) as excinfo:
            SoxAudioProcessor.check_availability()
        assert "Sox binary not found" in str(excinfo.value)
        assert SoxAudioProcessor._is_available is False


def test_tts_service_init_checks_sox():
    """Test that TTSService initialization fails if Sox is missing."""
    mock_engine = MagicMock()
    mock_cache = MagicMock()

    # We patch the class in the module where TTSService imports it
    with patch("src.services.tts_service.SoxAudioProcessor.check_availability") as mock_check:
        mock_check.side_effect = SoxNotFoundError("Sox not found")
        with pytest.raises(SoxNotFoundError):
            TTSService(mock_engine, mock_cache)
        mock_check.assert_called_once()


def test_apply_effects_calls_availability_check():
    """Test that apply_effects checks for Sox before running."""
    with patch("src.audio.processor.SoxAudioProcessor.check_availability") as mock_check:
        with patch("subprocess.run") as mock_run:
            SoxAudioProcessor.apply_effects("in.wav", "out.wav")
            mock_check.assert_called_once()
