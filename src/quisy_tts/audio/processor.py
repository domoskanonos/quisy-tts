import os
import time
from typing import Any

import numpy as np
import soundfile as sf

from quisy_tts.config import ProjectConfig

logger = ProjectConfig.get_logger()


class AudioProcessor:
    """Handles audio post-processing using native Python tools (soundfile/numpy)."""

    @staticmethod
    def concatenate_audio(input_paths: list[str], output_path: str) -> bool:
        """Concatenates multiple audio files using soundfile."""
        try:
            if not input_paths:
                logger.error("No input paths provided for concatenation.")
                return False

            logger.info(f"Concatenating {len(input_paths)} audio files to {output_path}")
            start_time = time.time()

            # Read all files and collect data and samplerates
            data_list = []
            samplerates = []

            for path in input_paths:
                data, sr = sf.read(path)
                data_list.append(data)
                samplerates.append(sr)

            if not data_list:
                return False

            # Ensure all files have the same samplerate (using the first one as reference)
            target_sr = samplerates[0]
            if any(sr != target_sr for sr in samplerates):
                logger.warning("Varying samplerates detected during concatenation. Using first file's rate.")

            # Concatenate arrays along the first axis
            combined_data = np.concatenate(data_list, axis=0)

            # Write the result
            sf.write(output_path, combined_data, target_sr)

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
