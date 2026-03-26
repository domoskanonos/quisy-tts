"""Lightweight local stub for `qwen_tts` used in tests/dev when the real
package is not installed. This allows importing the application without the
heavy external dependency. The real package provides Qwen3TTSModel with
generation methods; here we implement minimal, safe stubs.
"""

from typing import Any
import numpy as np


class Qwen3TTSModel:
    def __init__(self) -> None:
        pass

    @classmethod
    def from_pretrained(cls, *args: Any, **kwargs: Any) -> "Qwen3TTSModel":
        # Return a lightweight instance for development/testing.
        return cls()

    def generate_voice_design(
        self, text: str, language: str = "german", instruct: str = "", **kwargs
    ) -> tuple[list, int]:
        # Return a short silent waveform as numpy array and sample rate
        sr = 24000
        wav = np.zeros((1, int(0.01 * sr)), dtype=np.float32)
        return [wav], sr

    def generate_custom_voice(
        self, text: str, language: str = "german", speaker: str = "", instruct: str = "", **kwargs
    ) -> tuple[list, int]:
        sr = 24000
        wav = np.zeros((1, int(0.01 * sr)), dtype=np.float32)
        return [wav], sr

    def generate_voice_clone(
        self, text: str, language: str = "german", ref_audio: str | None = None, ref_text: str = "", **kwargs
    ) -> tuple[list, int]:
        sr = 24000
        wav = np.zeros((1, int(0.01 * sr)), dtype=np.float32)
        return [wav], sr
