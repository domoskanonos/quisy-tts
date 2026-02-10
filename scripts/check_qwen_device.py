import sys
import time
from pathlib import Path

import torch


# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig
from models.manager import ModelManager


def check_device() -> None:
    settings = ProjectConfig.get_settings()
    print(f"Configured DEVICE: {settings.DEVICE}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Current Device: {torch.cuda.get_device_name(0)}")

    print("Loading 0.6B model...")
    start = time.time()
    try:
        model = ModelManager.get_model(mode="base", size="0.6B")
        print(f"Model loaded in {time.time() - start:.2f}s")
        print(f"Model Device: {model.device}")
        print(f"Model Dtype: {model.dtype}")

        # Check a parameter specifically
        param = next(model.parameters())
        print(f"First Parameter Device: {param.device}")

    except Exception as e:
        print(f"Error loading model: {e}")


if __name__ == "__main__":
    check_device()
