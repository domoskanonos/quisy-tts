import subprocess
import time
import os
import shutil

import soundfile as sf
from typing import Any, Optional
from config import ProjectConfig

logger = ProjectConfig.get_logger()


class SoxNotFoundError(RuntimeError):
    """Raised when the Sox binary is not found on the system."""

    pass


class SoxAudioProcessor:
    """Handles audio post-processing using Sox."""

    _is_available: Optional[bool] = None

    @classmethod
    def check_availability(cls) -> None:
        """Checks if Sox is installed and in the PATH. Raises SoxNotFoundError if not."""
        if cls._is_available is True:
            return

        if shutil.which("sox") is None:
            cls._is_available = False
            msg = (
                "Sox binary not found. This application requires Sox for high-quality audio processing.\n"
                "Please install Sox via: 'choco install sox' (Windows), 'brew install sox' (macOS) or 'apt install sox' (Linux)."
            )
            logger.error(msg)
            raise SoxNotFoundError(msg)

        cls._is_available = True

    @staticmethod
    def apply_effects(input_path: str, output_path: str) -> bool:
        """Applies normalization and subtle effects to the audio using Sox."""
        SoxAudioProcessor.check_availability()
        try:
            command = [
                "sox",
                input_path,
                output_path,
                "norm",
                "-3",
                "treble",
                "1",
                "channels",
                "1",
            ]
            logger.info(f"Applying Sox post-processing: {' '.join(command)}")
            start_time = time.time()
            subprocess.run(command, check=True, capture_output=True)
            logger.debug(f"Sox processing took {time.time() - start_time:.4f}s")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Sox processing failed: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Error during Sox processing: {e}")
            return False

    @staticmethod
    def concatenate_audio(input_paths: list[str], output_path: str) -> bool:
        """Concatenates multiple audio files using Sox."""
        SoxAudioProcessor.check_availability()
        try:
            command = ["sox"] + input_paths + [output_path]
            logger.info(f"Concatenating audio with Sox: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Sox concatenation failed: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Error during Sox concatenation: {e}")
            return False


class AudioUtils:
    """Utilities for audio manipulation."""

    @staticmethod
    def save_waveform(waveform: Any, sr: int, path: str) -> None:
        """Saves a waveform tensor to a file."""
        # Accept both numpy arrays and torch tensors
        data = waveform
        # Lazy check for torch if it was intended to be used,
        # but in this context we just handle the waveform data.
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
