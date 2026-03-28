import torch
from diffusers import AudioLDM2Pipeline
import scipy.io.wavfile

# 1. Modell laden (nutzt float16 für weniger VRAM-Verbrauch)
model_id = "cvssp/audioldm2" # oder "cvssp/audioldm2-music" für Musik
pipe = AudioLDM2Pipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe.to("cuda") # Falls du eine NVIDIA GPU hast, sonst .to("cpu")

# 2. Beschreibung des Sounds
prompt = "A hammer hitting a metal plate in a large echoing warehouse"
negative_prompt = "low quality, noisy, music"

# 3. Sound generieren
# num_inference_steps: Höher = bessere Qualität (Standard 200)
# audio_length_in_s: Länge des Clips
audio = pipe(
    prompt, 
    negative_prompt=negative_prompt, 
    num_inference_steps=200, 
    audio_length_in_s=5.0
).audios[0]

# 4. Als WAV-Datei speichern
scipy.io.wavfile.write("output_sound.wav", rate=16000, data=audio)

print("Sound erfolgreich generiert: output_sound.wav")