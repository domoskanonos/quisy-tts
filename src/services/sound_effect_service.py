import torch
import torchaudio
from pathlib import Path
from transformers import AudioGenForConditionalGeneration, AutoProcessor
from config import ProjectConfig

logger = ProjectConfig.get_logger()


class SoundEffectService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading AudioGen on {self.device}...")
        try:
            self.processor = AutoProcessor.from_pretrained("facebook/audiogen-medium")
            self.model = AudioGenForConditionalGeneration.from_pretrained("facebook/audiogen-medium").to(self.device)
        except Exception as e:
            logger.error(f"Failed to load AudioGen: {e}")
            raise

    async def generate(self, description: str) -> Path:
        logger.info(f"Generating sound effect: {description}")
        inputs = self.processor(
            text=[description],
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            audio_values = self.model.generate(**inputs, max_new_tokens=512)

        audio_values = audio_values.squeeze().cpu()

        import hashlib

        sfx_key = hashlib.sha256(description.encode()).hexdigest()[:12]
        output_path = self.output_dir / f"sfx_{sfx_key}.wav"

        torchaudio.save(str(output_path), audio_values.unsqueeze(0), 16000)
        logger.info(f"Generated sound effect saved to {output_path}")
        return output_path
