import subprocess
import time

import soundfile as sf
from typing import Any

from typing import Any, Optional

# Import torch lazily in functions that need it to allow running tests without
# an installed torch wheel in lightweight environments
torch: Optional[Any] = None
try:
    import torch as _torch

    torch = _torch
except ImportError:
    pass

from config import ProjectConfig


logger = ProjectConfig.get_logger()


class SoxAudioProcessor:
    """Handles audio post-processing using Sox."""

    @staticmethod
    def apply_effects(input_path: str, output_path: str) -> bool:
        """Applies normalization and subtle effects to the audio using Sox."""
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
        except FileNotFoundError:
            logger.error("Sox binary not found. Please ensure 'sox' is installed and in PATH.")
            return False
        except Exception as e:
            logger.error(f"Error during Sox processing: {e}")
            return False


class AudioUtils:
    """Utilities for audio manipulation."""

    @staticmethod
    def save_waveform(waveform: Any, sr: int, path: str) -> None:
        """Saves a waveform tensor to a file."""
        # Accept both numpy arrays and torch tensors
        data = waveform
        if torch is not None and hasattr(waveform, "cpu"):
            data = waveform.squeeze().cpu().numpy()
        elif hasattr(waveform, "squeeze") and not isinstance(waveform, (bytes, str)):
            try:
                data = waveform.squeeze()
            except Exception:
                pass

        sf.write(path, data, sr)
