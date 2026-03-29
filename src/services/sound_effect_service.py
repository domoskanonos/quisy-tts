import torch
from diffusers.pipelines.audioldm2.pipeline_audioldm2 import AudioLDM2Pipeline
from transformers import GPT2LMHeadModel
import scipy.io.wavfile
import numpy as np
from pathlib import Path
import hashlib
from datetime import datetime
import asyncio
from typing import Optional


class SoundEffectService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_id = "cvssp/audioldm2-large"
        self.pipe: Optional[AudioLDM2Pipeline] = None

    def _load_model(self):
        """Lazy load the model to avoid heavy lifting in constructor."""
        if self.pipe is not None:
            return

        print(f"Loading model {self.model_id}...")
        lang_model = GPT2LMHeadModel.from_pretrained(
            self.model_id, subfolder="language_model", dtype=torch.float16
        )

        self.pipe = AudioLDM2Pipeline.from_pretrained(
            self.model_id, language_model=lang_model, dtype=torch.float16
        )

        self.pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        print("Model loaded successfully.")

    async def generate(self, prompt: str) -> Path:
        """Generate audio from prompt."""
        # Ensure model is loaded (in a thread to not block if first load takes time)
        if self.pipe is None:
            await asyncio.to_thread(self._load_model)

        # Run inference in a thread to keep the event loop responsive
        def _run_inference():
            if(self.pipe is None):
                raise RuntimeError("Model pipeline is not loaded.")
            output = self.pipe(
                prompt,
                num_inference_steps=50,
                guidance_scale=3.5,
            )
            # AudioLDM2Pipeline may return a tuple or dict; handle accordingly
            if output is None:
                raise RuntimeError("Inference did not return any audio.")
            # Try to extract audio from output
            if isinstance(output, dict) and "audios" in output and len(output["audios"]) > 0:
                return output["audios"][0]
            elif isinstance(output, (tuple, list)) and len(output) > 0:
                return output[0]
            elif hasattr(output, "audios") and len(output.audios) > 0:
                return output.audios[0]
            else:
                raise RuntimeError("Inference did not return any audio.")

        audio = await asyncio.to_thread(_run_inference)

        # Post-process
        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)

        # Generate unique filename
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sfx_{prompt_hash}_{timestamp}.wav"
        output_path = self.output_dir / filename

        # Save
        scipy.io.wavfile.write(str(output_path), rate=16000, data=audio_int16)

        return output_path
