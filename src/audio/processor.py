import os
import time
from typing import Any

from pydub import AudioSegment
from config import ProjectConfig

logger = ProjectConfig.get_logger()


class AudioProcessor:
    """Handles audio post-processing using native Python tools (soundfile/numpy)."""

    @staticmethod
    def concatenate_audio(input_paths: list[str], output_path: str) -> bool:
        """Concatenates multiple audio files using pydub."""
        try:
            if not input_paths:
                logger.error("No input paths provided for concatenation.")
                return False

            logger.info(f"Concatenating {len(input_paths)} audio files to {output_path}")
            start_time = time.time()

            combined = AudioSegment.empty()
            for path in input_paths:
                combined += AudioSegment.from_wav(path)

            combined.export(output_path, format="wav")

            logger.debug(f"Concatenation took {time.time() - start_time:.4f}s")
            return True
        except Exception as e:
            logger.error(f"Error during audio concatenation: {e}")
            return False


class AudioUtils:
    """Utilities for audio manipulation."""

    @staticmethod
    def save_waveform(waveform: Any, sr: int, path: str) -> None:
        """Saves a waveform tensor to a file."""
        # Accept both numpy arrays and torch tensors
        import soundfile as sf

        data = waveform
        if hasattr(waveform, "cpu"):
            data = waveform.squeeze().cpu().numpy()
        elif hasattr(waveform, "squeeze") and not isinstance(waveform, (bytes, str)):
            try:
                data = waveform.squeeze()
            except Exception:
                pass

        logger.info(f"Saving waveform with shape: {data.shape if hasattr(data, 'shape') else 'unknown'}")
        sf.write(path, data, sr)

        # Verify the file was written successfully
        if os.path.exists(path) and os.path.getsize(path) == 0:
            logger.error(f"Saved audio file {path} is empty (0 bytes).")
            raise IOError(f"Audio file {path} is empty.")
        elif not os.path.exists(path):
            logger.error(f"Failed to create audio file {path}.")
            raise IOError(f"Audio file {path} was not created.")
