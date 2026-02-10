import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig
from models.manager import ModelManager


def test_device_validation() -> None:
    logger = ProjectConfig.get_logger()
    logger.info("=== Testing Device Validation ===")

    # Mock settings to force CUDA
    with patch("models.manager.ProjectConfig") as mock_config:
        mock_settings = MagicMock()
        mock_settings.DEVICE = "cuda"
        mock_config.get_settings.return_value = mock_settings
        mock_config.get_logger.return_value = logger

        # Mock torch.cuda.is_available to return False
        with patch("torch.cuda.is_available", return_value=False):
            logger.info("Attempting to load model with DEVICE='cuda' and no available GPU...")
            try:
                ModelManager.get_model()
            except RuntimeError as e:
                logger.info(f"Caught expected error: {e}")
                if "CUDA unavailable but requested" in str(e):
                    logger.info("SUCCESS: Verification passed.")
                else:
                    logger.error("FAILURE: Incorrect error message.")
            except Exception as e:
                logger.error(f"FAILURE: Caught unexpected exception: {type(e).__name__}: {e}")
            else:
                logger.error("FAILURE: No exception raised.")


if __name__ == "__main__":
    test_device_validation()
