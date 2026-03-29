import torch
#from diffusers import AudioLDMPipeline
from diffusers.pipelines.audioldm2.pipeline_audioldm2 import AudioLDM2Pipeline
import scipy.io.wavfile

# 1. Modell laden
# AudioLDM-M-Full ist ein robustes Modell für Sound-Effekte
model_id = "cvssp/audioldm-m-full"
#pipe = AudioLDMPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = AudioLDM2Pipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# 2. Beschreibung des Sounds
prompt = "A hammer hitting a metal plate in a large echoing warehouse"

# 3. Sound generieren
# AudioLDM liefert direkt ein audio array zurück
output = pipe(
    prompt,
    num_inference_steps=50,
)
# Audio-Daten extrahieren
audio = output.audios[0]

# 4. Als WAV-Datei speichern
# AudioLDM nutzt standardmäßig 16kHz
scipy.io.wavfile.write("output_sound.wav", rate=16000, data=audio)

print("Sound erfolgreich generiert: output_sound.wav")
