import subprocess

import soundfile as sf
import torch

from project.config import ProjectConfig


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
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Sox processing failed: {e.stderr.decode()}")
            return False
        except FileNotFoundError:
            logger.error(
                "Sox binary not found. Please ensure 'sox' is installed and in PATH."
            )
            return False
        except Exception as e:
            logger.error(f"Error during Sox processing: {e}")
            return False


class AudioUtils:
    """Utilities for audio manipulation."""

    @staticmethod
    def concatenate_audio_segments(segments: list[torch.Tensor]) -> torch.Tensor:
        """Concatenates multiple audio tensors."""
        if not segments:
            return torch.zeros((1, 0))
        return torch.cat(segments, dim=1)

    @staticmethod
    def save_waveform(waveform: torch.Tensor, sr: int, path: str):
        """Saves a waveform tensor to a file."""
        sf.write(path, waveform.squeeze().cpu().numpy(), sr)
