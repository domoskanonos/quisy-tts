import torch
import torchaudio
from pathlib import Path
from audiocraft.models import AudioGen
from config import ProjectConfig

logger = ProjectConfig.get_logger()


class SoundEffectService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading AudioGen on {self.device}...")
        try:
            self.model = AudioGen.get_pretrained("facebook/audiogen-medium")
            self.model.set_generation_params(duration=5)
        except Exception as e:
            logger.error(f"Failed to load AudioGen: {e}")
            raise

    async def generate(self, description: str) -> Path:
        logger.info(f"Generating sound effect: {description}")
        with torch.no_grad():
            wav = self.model.generate([description], progress=True)

        audio_values = wav.squeeze().cpu()

        import hashlib

        sfx_key = hashlib.sha256(description.encode()).hexdigest()[:12]
        output_path = self.output_dir / f"sfx_{sfx_key}.wav"

        torchaudio.save(str(output_path), audio_values.unsqueeze(0), 16000)
        logger.info(f"Generated sound effect saved to {output_path}")
        return output_path
