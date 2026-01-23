import os
import re
import subprocess
import traceback

import soundfile as sf
import torch
from pydantic import BaseModel
from qwen_tts import Qwen3TTSModel

from project.config import ProjectConfig


logger = ProjectConfig.get_logger()


class TTSParams(BaseModel):
    """Parameters for TTS generation."""

    language_id: str = "de"
    reference_audio: str | None = None
    ref_text: str | None = None
    speed: float = 1.0


class NaturalOptimizer:
    """Stub for text optimization."""

    def optimize(self, text: str) -> str:
        # Basic cleaning for now
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text



class SoxAudioProcessor:
    """Handles audio post-processing using Sox."""

    @staticmethod
    def apply_effects(input_path: str, output_path: str) -> bool:
        """Applies normalization and subtle effects to the audio."""
        try:
            # Example: normalize to -3dB and apply a slight treble boost
            # --norm=-3: normalize to -3dB
            # treble 1: slight treble boost for clarity
            command = [
                "sox",
                input_path,
                output_path,
                "norm",
                "-3",
                "treble",
                "1",
                "channels",
                "1",
            ]
            logger.info(f"Applying Sox post-processing: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Sox processing failed: {e.stderr.decode()}")
            return False
        except FileNotFoundError:
            logger.error(
                "Sox binary not found. Please ensure 'sox' is installed and in PATH."
            )
            return False
        except Exception as e:
            logger.error(f"Error during Sox processing: {e}")
            return False


class AudioUtils:
    """Utilities for audio manipulation."""

    @staticmethod
    def concatenate_audio_segments(
        segments: list[torch.Tensor], sr: int
    ) -> torch.Tensor:
        if not segments:
            return torch.zeros((1, 0))
        # Concatenate on the time dimension
        return torch.cat(segments, dim=1)


class QwenTextToSpeech:
    _shared_model = None
    _sr = 24000  # Default sample rate

    def __init__(self):
        self.settings = ProjectConfig.get_settings()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    @classmethod
    def initialize(cls, device=None):
        if cls._shared_model is None:
            settings = ProjectConfig.get_settings()
            logger.info(f"Initializing Qwen3-TTS model: {settings.MODEL_NAME}...")

            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"

            try:
                # Use bfloat16 for better precision on newer NVIDIA cards
                # float16 is also common, but bfloat16 is preferred if supported
                if "cuda" in str(device):
                    # Check if device supports bfloat16 (mostly RTX 30+ and A100+)
                    if torch.cuda.get_device_capability(0)[0] >= 8:
                        dtype = torch.bfloat16
                    else:
                        dtype = torch.float16
                    logger.info(f"Using {dtype} for GPU acceleration.")
                else:
                    dtype = torch.float32

                cls._shared_model = Qwen3TTSModel.from_pretrained(
                    settings.MODEL_NAME,
                    device_map=device,
                    torch_dtype=dtype,  # Correct parameter name usually torch_dtype
                )
                logger.info(
                    f"Qwen3-TTS model '{settings.MODEL_NAME}' initialized on {device}."
                )

                # Ensure directories exist
                os.makedirs(settings.VOICES_DIR, exist_ok=True)
                os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

            except Exception as e:
                logger.error(f"Failed to initialize Qwen3-TTS: {e}")
                raise

    @classmethod
    def get_model(cls, device=None):
        if cls._shared_model is None:
            cls.initialize(device)
        return cls._shared_model

    def _get_default_reference(self) -> tuple[torch.Tensor, int] | tuple[None, None]:
        """Try to find a default reference audio in the voices directory."""
        # Common default names or just the first wav found
        preferred = ["alexandra_bogensperger.wav", "dominik_bruhn.wav", "Sonia.wav"]
        for p in preferred:
            path = os.path.join(self.settings.VOICES_DIR, p)
            if os.path.exists(path):
                try:
                    data, sr = sf.read(path)
                    return data, sr
                except:
                    pass

        # Fallback to any wav
        if os.path.exists(self.settings.VOICES_DIR):
            for f in os.listdir(self.settings.VOICES_DIR):
                if f.lower().endswith(".wav"):
                    path = os.path.join(self.settings.VOICES_DIR, f)
                    try:
                        data, sr = sf.read(path)
                        return data, sr
                    except:
                        pass
        return None, None

    def generate_audio(
        self, text: str, params: TTSParams | None = None, segment_callback=None
    ) -> torch.Tensor | None:
        if params is None:
            params = TTSParams()

        logger.info(f"🎯 Generating audio for text: '{text}'")

        optimizer = NaturalOptimizer()
        text = optimizer.optimize(text)

        # Split by punctuation
        segments = [
            s.strip() for s in re.split(r"(?<=[\.\!\?\:\;])\s+", text) if s.strip()
        ]
        logger.info(f"📝 Text split into {len(segments)} segment(s)")

        model = self.get_model()
        audio_segments = []
        current_sr = self._sr

        session_language = "German" if params.language_id == "de" else "English"

        # Load reference audio
        ref_audio_tuple = None
        if params.reference_audio:
            ref_path = os.path.join(self.settings.VOICES_DIR, params.reference_audio)
            if os.path.exists(ref_path):
                try:
                    ref_data, rsr = sf.read(ref_path)
                    if ref_data.ndim > 1:
                        ref_data = ref_data.mean(axis=1)
                    ref_audio_tuple = (ref_data, rsr)
                    logger.info(f"Loaded reference audio from {ref_path}")
                except Exception as e:
                    logger.warning(f"Could not load reference audio {ref_path}: {e}")
            else:
                logger.warning(f"Reference audio not found at {ref_path}")

        # If still no reference, use default
        if ref_audio_tuple is None:
            logger.info(
                "No reference provided/found. Attempting to use a default voice."
            )
            d_data, d_sr = self._get_default_reference()
            if d_data is not None:
                if d_data.ndim > 1:
                    d_data = d_data.mean(axis=1)
                ref_audio_tuple = (d_data, d_sr)
                logger.info("Using default reference audio.")

        if ref_audio_tuple is None:
            logger.error(
                "Absolutely no reference audio available. Generation will likely fail."
            )

        for i, segment in enumerate(segments):
            logger.info(
                f"🎵 Generating audio for segment {i + 1}/{len(segments)}: {segment}"
            )

            try:
                # IMPORTANT: ref_audio must be a tuple (audio_data_numpy, sample_rate)
                # and NOT a string path.
                if ref_audio_tuple:
                    if params.ref_text:
                        wavs, sr = model.generate_voice_clone(
                            text=segment,
                            language=session_language,
                            ref_audio=ref_audio_tuple,
                            ref_text=params.ref_text,
                        )
                    else:
                        wavs, sr = model.generate_voice_clone(
                            text=segment,
                            language=session_language,
                            ref_audio=ref_audio_tuple,
                            x_vector_only_mode=True,
                        )
                else:
                    # Last resort fallback (unlikely to work without prompt/ref)
                    wavs, sr = model.generate_voice_clone(
                        text=segment,
                        language=session_language,
                    )

                current_sr = sr
                self.__class__._sr = sr

                if isinstance(wavs, (list, tuple)) and len(wavs) > 0:
                    wav = wavs[0]
                else:
                    wav = wavs

                if not isinstance(wav, torch.Tensor):
                    wav = torch.from_numpy(wav)

                if wav.ndim == 1:
                    wav = wav.unsqueeze(0)

                audio_segments.append(wav)
                if segment_callback:
                    segment_callback(wav, i, len(segments))

            except Exception as e:
                logger.error(f"Error generating audio for segment {i}: {e}")
                logger.error(traceback.format_exc())
                continue

        if not audio_segments:
            logger.error("No audio generated.")
            return None

        final_audio = AudioUtils.concatenate_audio_segments(audio_segments, current_sr)
        logger.info(f"✅ Audio generation completed: {final_audio.shape[1]} samples")
        return final_audio

    def generate_and_save(
        self, text: str, output_path: str, params: TTSParams | None = None
    ) -> str | None:
        wav = self.generate_audio(text, params)
        if wav is not None:
            # Save raw output first
            raw_path = output_path.replace(".wav", "_raw.wav")
            wav_np = (
                wav.squeeze().cpu().numpy() if isinstance(wav, torch.Tensor) else wav
            )
            sf.write(raw_path, wav_np, self._sr)
            logger.info(f"Raw audio saved to: {raw_path}")

            # Apply Sox post-processing
            if SoxAudioProcessor.apply_effects(raw_path, output_path):
                logger.info(f"Post-processed audio saved to: {output_path}")
                # Clean up raw file
                try:
                    os.remove(raw_path)
                except:
                    pass
                return output_path
            else:
                # If Sox fails, fallback to raw output
                logger.warning("Sox failed, falling back to raw audio.")
                try:
                    os.replace(raw_path, output_path)
                except Exception as e:
                    logger.error(f"Failed to replace raw file: {e}")
                    return raw_path  # Return raw path if replace fails
                return output_path
        return None

    @property
    def sr(self) -> int:
        return self._sr
