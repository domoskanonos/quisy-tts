import os
import sys
from concurrent.futures import ThreadPoolExecutor

from huggingface_hub import snapshot_download


# Disable progress bars to avoid thread-safety issues with tqdm in parallel downloads
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"


# Add src to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from project.config import ProjectConfig


def download_model(model_id: str, models_dir: str):
    print(f"Starting download of {model_id}...")
    try:
        local_dir = os.path.join(models_dir, model_id.replace("/", "--"))
        snapshot_download(
            repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False
        )
        print(f"Successfully downloaded {model_id} to {local_dir}")
    except Exception as e:
        print(f"Failed to download {model_id}: {e}")


def main():
    settings = ProjectConfig.get_settings()
    models_to_download = [
        m.strip() for m in settings.DOWNLOAD_MODELS.split(",") if m.strip()
    ]
    models_dir = os.path.abspath(settings.MODELS_DIR)

    os.makedirs(models_dir, exist_ok=True)

    print(
        f"Downloading {len(models_to_download)} models to {models_dir} in parallel..."
    )

    with ThreadPoolExecutor(max_workers=len(models_to_download)) as executor:
        for model_id in models_to_download:
            executor.submit(download_model, model_id, models_dir)


if __name__ == "__main__":
    main()
