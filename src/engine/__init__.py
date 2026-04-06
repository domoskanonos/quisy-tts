"""Engine package - qwen-tts based TTS adapter (Infrastructure layer)."""

from core.interfaces import TTSEngineInterface
from engine.qwen import QwenTextToSpeech

__all__ = ["TTSEngineInterface", "QwenTextToSpeech"]
