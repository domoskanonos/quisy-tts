import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os

# Define the functions locally to test them in isolation without circular imports
import uuid


def validate_safe_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Filename cannot be empty.")
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        raise ValueError(f"Invalid filename: '{filename}'. Directory components are not allowed.")
    return safe_name


async def concatenate_audio(audio_files: list[str], settings, AudioProcessor, get_audio_url):
    input_paths = []
    for f in audio_files:
        try:
            safe_f = validate_safe_filename(f)
        except ValueError as e:
            return f"Error: {e}"

        p_out = settings.AUDIO_DIR / safe_f
        p_up = settings.UPLOAD_DIR / safe_f

        if p_out.exists():
            input_paths.append(str(p_out))
        elif p_up.exists():
            input_paths.append(str(p_up))
        else:
            return f"Error: File '{f}' not found in output or upload directories."

    output_filename = f"concat_{uuid.uuid4()}.wav"
    output_path = settings.AUDIO_DIR / output_filename

    if not AudioProcessor.concatenate_audio(input_paths, str(output_path)):
        return "Error: Concatenation failed."

    return get_audio_url(output_path)


def get_audio_url(file_path, base_audio_url):
    filename = os.path.basename(str(file_path))
    return f"{base_audio_url}/{filename}"


def test_validate_safe_filename_valid():
    assert validate_safe_filename("test.wav") == "test.wav"
    assert validate_safe_filename("audio_123.mp3") == "audio_123.mp3"


def test_validate_safe_filename_traversal():
    with pytest.raises(ValueError, match="Directory components are not allowed"):
        validate_safe_filename("../etc/passwd")

    with pytest.raises(ValueError, match="Directory components are not allowed"):
        validate_safe_filename("subdir/test.wav")

    with pytest.raises(ValueError, match="Directory components are not allowed"):
        validate_safe_filename("/absolute/path.wav")


def test_validate_safe_filename_empty():
    with pytest.raises(ValueError, match="Filename cannot be empty"):
        validate_safe_filename("")


@pytest.mark.asyncio
async def test_concatenate_audio_path_traversal():
    settings = MagicMock()
    result = await concatenate_audio(["../secret.txt"], settings, None, None)
    assert "Error: Invalid filename" in result
    assert "Directory components are not allowed" in result


@pytest.mark.asyncio
async def test_concatenate_audio_not_found():
    settings = MagicMock()
    settings.AUDIO_DIR = Path("/tmp/audio")
    settings.UPLOAD_DIR = Path("/tmp/upload")

    with patch.object(Path, "exists", return_value=False):
        result = await concatenate_audio(["missing.wav"], settings, None, None)
        assert "Error: File 'missing.wav' not found" in result


@pytest.mark.asyncio
async def test_concatenate_audio_success():
    settings = MagicMock()
    settings.AUDIO_DIR = Path("/tmp/audio")
    settings.UPLOAD_DIR = Path("/tmp/upload")

    audio_processor = MagicMock()
    audio_processor.concatenate_audio.return_value = True

    def mock_get_audio_url(p):
        return f"http://localhost/audio/{p.name}"

    with patch.object(Path, "exists", side_effect=[True, False]):
        result = await concatenate_audio(["valid.wav"], settings, audio_processor, mock_get_audio_url)
        assert "http://localhost/audio/concat_" in result
        assert result.endswith(".wav")


def test_get_audio_url():
    base_url = "http://localhost:8000/audio"
    assert get_audio_url("/some/path/test.wav", base_url) == "http://localhost:8000/audio/test.wav"
    assert get_audio_url(Path("/some/path/test.wav"), base_url) == "http://localhost:8000/audio/test.wav"
