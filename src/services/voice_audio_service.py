import logging
from pathlib import Path
from domain.voice.models import Voice

logger = logging.getLogger("project")


class VoiceAudioService:
    """Service for handling voice audio files on disk."""

    def __init__(self, voices_dir: Path) -> None:
        self._voices_dir = voices_dir
        self._voices_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_filename(voice_id: str) -> str:
        return Voice.get_filename(voice_id)

    def delete_audio(self, voice_id: str) -> None:
        audio_path = self._voices_dir / self.get_filename(voice_id)
        if audio_path.exists():
            audio_path.unlink()
            logger.info(f"Audio file deleted: {audio_path}")

    def save_audio(self, voice_id: str, audio_data: bytes) -> str:
        final_filename = self.get_filename(voice_id)
        audio_path = self._voices_dir / final_filename
        audio_path.write_bytes(audio_data)
        logger.info(f"Audio saved for voice {voice_id}: {final_filename}")
        return final_filename

    def get_audio_path(self, voice_id: str, filename: str | None) -> Path | None:
        if not filename:
            return None
        audio_path = self._voices_dir / filename
        return audio_path if audio_path.exists() else None
