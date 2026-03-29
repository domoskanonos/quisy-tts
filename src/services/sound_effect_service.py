import torch
from diffusers.pipelines.audioldm2.pipeline_audioldm2 import AudioLDM2Pipeline
from transformers import GPT2LMHeadModel
import scipy.io.wavfile
import numpy as np

# 1. Modell laden
# AudioLDM2-Music ist super, für Soundeffekte wie Hundegebell 
# ist "audioldm2-full" oft noch einen Tick realistischer.
model_id = "cvssp/audioldm2-large" 

# Fix für den AttributeError (GPT2Model vs GPT2LMHeadModel)
lang_model = GPT2LMHeadModel.from_pretrained(
    model_id, 
    subfolder="language_model", 
    torch_dtype=torch.float16
)

pipe = AudioLDM2Pipeline.from_pretrained(
    model_id, 
    language_model=lang_model, 
    torch_dtype=torch.float16
)

pipe.to("cuda" if torch.cuda.is_available() else "cpu")

# 2. Beschreibung des Sounds
prompt = "a close-up, realistic recording of a large dog barking aggressively"

prompt = " ein realistisch klingendes, aggressives Hundegebell, aufgenommen aus der Nähe"

# 3. Sound generieren
# Wir nutzen .audios[0], um direkt an das Numpy-Array zu kommen
output = pipe(
    prompt,
    num_inference_steps=50,
    guidance_scale=3.5,
)
audio = output.audios[0]

# --- FIX FÜR DEN STRUCT-ERROR (Konvertierung) ---
# 1. Sicherstellen, dass die Daten im Bereich -1.0 bis 1.0 liegen
audio = np.clip(audio, -1.0, 1.0)

# 2. Skalieren auf 16-Bit Integer Bereich und Typ umwandeln
# Dies löst den Fehler: struct.error: 'H' format requires 0 <= number <= 65535
audio_int16 = (audio * 32767).astype(np.int16)

# 4. Als WAV-Datei speichern
# AudioLDM2 arbeitet intern mit 16000Hz
scipy.io.wavfile.write("output_sound.wav", rate=16000, data=audio_int16)

print("Sound erfolgreich generiert und im int16-Format gespeichert: output_sound.wav")