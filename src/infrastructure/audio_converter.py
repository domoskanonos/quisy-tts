"""Infrastructure implementation for audio conversion.

Provides concrete implementations for audio format conversions using external libraries.
"""

from pathlib import Path
from pydub import AudioSegment
from src.core.interfaces import AudioConverter


class PydubAudioConverter(AudioConverter):
    """Concrete implementation of AudioConverter using the pydub library."""

    def convert_to_mp3(self, input_path: Path) -> Path:
        """Converts an audio file to MP3 format using pydub.

        Args:
            input_path: Path to the input audio file (typically WAV).

        Returns:
            Path to the resulting MP3 file.
        """
        mp3_path = input_path.with_suffix(".mp3")
        audio = AudioSegment.from_wav(str(input_path))
        audio.export(str(mp3_path), format="mp3")
        return mp3_path
