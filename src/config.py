import logging
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """Project settings using Pydantic."""

    PROJECT_NAME: str = "quisy-tts"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8045

    # Base directory for all data
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    BASE_DATA_DIR: Path = BASE_DIR / "data"

    # TTS Settings
    MODEL: str = "0.6"
    DEFAULT_VOICE_ID: str | None = None
    DEFAULT_LANGUAGE: str = "german"

    # Base URL for constructing accessible audio URLs (avoid 0.0.0.0 in responses)
    BASE_URL: str = "http://localhost:8045"

    @property
    def DEFAULT_MODEL_SIZE(self) -> str:
        if self.MODEL == "1.7":
            return "1.7B"
        if self.MODEL == "0.6":
            return "0.6B"
        raise ValueError(f"Unsupported model version: {self.MODEL}")

    @property
    def MODELS_TO_DOWNLOAD(self) -> list[str]:
        if self.MODEL == "1.7":
            return [
                "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            ]
        if self.MODEL == "0.6":
            return [
                "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
                "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            ]
        raise ValueError(f"Unsupported model version: {self.MODEL}")

    @property
    def MODELS_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "models"

    @property
    def VOICES_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "voices"

    @property
    def AUDIO_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "audio"

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.AUDIO_DIR / "uploads"

    @property
    def APP_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "database"

    @property
    def RESOURCES_DIR(self) -> Path:
        return self.BASE_DIR / "resources"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProjectConfig:
    """Central configuration access point for the project.

    Provides cached access to ProjectSettings and a central logger.
    Startup validation that requires I/O (e.g. DB checks) is handled
    in the application lifespan, not here (separation of concerns).
    """

    _settings: ProjectSettings | None = None
    _logger: logging.Logger | None = None

    @classmethod
    def get_settings(cls) -> ProjectSettings:
        if cls._settings is None:
            cls._settings = ProjectSettings()
        assert cls._settings is not None
        return cls._settings

    @classmethod
    def reset(cls) -> None:
        cls._settings = None
        cls._logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            cls._logger = logging.getLogger("project")
            cls._logger.setLevel(cls.get_settings().LOG_LEVEL)
        assert cls._logger is not None
        return cls._logger


def validate_startup_config() -> None:
    """Validate runtime config that requires I/O (called from lifespan).

    Checks DEFAULT_VOICE_ID against the resources DB if set, and fails
    fast with a clear message on misconfiguration.
    """
    import sqlite3

    settings = ProjectConfig.get_settings()
    default_voice_id = settings.DEFAULT_VOICE_ID
    if not default_voice_id:
        return

    resource_db = settings.RESOURCES_DIR / "quisy-tts.db"
    if not resource_db.exists():
        sys.stderr.write(
            f"ERROR: DEFAULT_VOICE_ID is set to '{default_voice_id}', but resources DB was not found at: {resource_db}\n"
        )
        raise SystemExit(1)

    try:
        with resource_db.open("ab"):
            pass
    except OSError as e:
        sys.stderr.write(f"ERROR: resources DB '{resource_db}' is not writable: {e}\n")
        raise SystemExit(1) from e

    try:
        conn = sqlite3.connect(str(resource_db))
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM voices WHERE voice_id = ? LIMIT 1", (default_voice_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            sys.stderr.write(
                f"ERROR: DEFAULT_VOICE_ID='{default_voice_id}' not found in resources DB '{resource_db}'.\n"
            )
            raise SystemExit(1)
    except sqlite3.Error as e:
        sys.stderr.write(f"ERROR: Failed to query resources DB '{resource_db}': {e}\n")
        raise SystemExit(1) from e
