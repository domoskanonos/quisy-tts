import torch
import torchaudio
from pathlib import Path
from diffusers.pipelines.audioldm2.pipeline_audioldm2 import AudioLDM2Pipeline
from config import ProjectConfig

logger = ProjectConfig.get_logger()


class SoundEffectService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading AudioLDM2 on {self.device}...")
        try:
            # We use float16 if cuda is available for better performance/memory usage
            dtype = torch.float16 if self.device == "cuda" else torch.float32
            self.pipe = AudioLDM2Pipeline.from_pretrained("cvssp/audioldm2", torch_dtype=dtype)
            self.pipe.to(self.device)
        except Exception as e:
            logger.error(f"Failed to load AudioLDM2: {e}")
            raise

    async def generate(self, description: str) -> Path:
        logger.info(f"Generating sound effect: {description}")
        with torch.no_grad():
            # Adjust num_inference_steps if generation is too slow
            audio = self.pipe(description, num_inference_steps=50).audios[0]

        import hashlib

        sfx_key = hashlib.sha256(description.encode()).hexdigest()[:12]
        output_path = self.output_dir / f"sfx_{sfx_key}.wav"

        # The pipe returns a numpy array, we need to convert to tensor for torchaudio
        audio_tensor = torch.from_numpy(audio).unsqueeze(0)

        # AudioLDM2 usually outputs at 16000Hz
        torchaudio.save(str(output_path), audio_tensor, 16000)
        logger.info(f"Generated sound effect saved to {output_path}")
        return output_path
