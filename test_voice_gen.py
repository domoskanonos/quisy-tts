import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger("test")


# Mock classes for testing
class MockSettings:
    def __init__(self):
        self.VOICES_DIR = Path("voices")
        self.AUDIO_DIR = Path("audio")
        self.DEFAULT_VOICE_ID = "default_003-1"


class MockConfig:
    @staticmethod
    def get_logger():
        return logger

    @staticmethod
    def get_settings():
        return MockSettings()


# Need to import the actual services
# Adjust sys.path to include src
sys.path.append(str(Path("src").absolute()))

from services.voice_audio_integrity import VoiceAudioIntegrityService
from services.voice_service import VoiceService
from engine.qwen import QwenTextToSpeech


async def test_generation():
    # Setup
    settings = MockSettings()
    settings.VOICES_DIR.mkdir(exist_ok=True)
    settings.AUDIO_DIR.mkdir(exist_ok=True)

    # Use a dummy database/service that returns the voice
    class MockVoiceService(VoiceService):
        def get_voice(self, voice_id):
            return {
                "id": "default_003-1",
                "example_text": "Dies ist ein Test.",
                "language": "german",
                "instruct": "Test voice",
                "audio_filename": None,
            }

        def set_audio(self, voice_id, data, filename):
            print(f"DEBUG: set_audio called for {voice_id}")

    voice_service = MockVoiceService(settings.VOICES_DIR)
    engine = QwenTextToSpeech()

    # Integrity service
    integrity = VoiceAudioIntegrityService(voice_service, engine, None)  # CacheService might be hard to mock

    print("DEBUG: Calling ensure_audio")
    await integrity.ensure_audio("default_003-1", force=True)
    print("DEBUG: ensure_audio finished")


if __name__ == "__main__":
    asyncio.run(test_generation())
