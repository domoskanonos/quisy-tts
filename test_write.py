import soundfile as sf
import numpy as np
from pathlib import Path

# Create a dummy waveform
sr = 24000
waveform = np.random.uniform(-1, 1, sr)
path = Path("data/voices/voice_default_003-1.wav")
path.parent.mkdir(parents=True, exist_ok=True)

try:
    sf.write(path, waveform, sr)
    print(f"Successfully wrote {path}")
except Exception as e:
    print(f"Failed to write {path}: {e}")
