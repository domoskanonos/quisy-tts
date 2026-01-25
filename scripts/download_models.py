import os
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


# Disable progress bars to avoid thread-safety issues with tqdm in parallel downloads
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from project.config import ProjectConfig


def download_model(model_id: str, models_dir: Path) -> None:
    """Downloads a single model from Hugging Face."""
    print(f"Starting download of {model_id}...")
    try:
        local_dir = models_dir / model_id.replace("/", "--")
        snapshot_download(
            repo_id=model_id, local_dir=str(local_dir), local_dir_use_symlinks=False
        )
        print(f"Successfully downloaded {model_id} to {local_dir}")
    except Exception as e:
        print(f"Failed to download {model_id}: {e}")


def main() -> None:
    """Main downloader loop."""
    settings = ProjectConfig.get_settings()
    models_to_download = [
        m.strip()
        for m in settings.DOWNLOAD_MODELS.replace("\n", "").split(",")
        if m.strip()
    ]
    models_dir = settings.MODELS_DIR.resolve()
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(models_to_download)} models to {models_dir}...")

    for model_id in models_to_download:
        download_model(model_id, models_dir)


if __name__ == "__main__":
    main()
