import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """Project settings using Pydantic."""

    # Example settings with default values
    # These can be overridden by environment variables (e.g. PROJECT_NAME)
    PROJECT_NAME: str = "cosmo-tts"
    LOG_LEVEL: str = "INFO"
    DEVICE: str = "cuda"  # "cuda" or "cpu"

    # TTS Settings
    DEFAULT_MODEL_SIZE: str = "1.7B"  # "1.7B" or "0.6B"
    DOWNLOAD_MODELS: str = (
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base,"
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign,"
        "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice,"
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base,"
        "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
    )
    MODELS_DIR: str = "models"
    VOICES_DIR: str = "voices"
    OUTPUT_DIR: str = "output"
    DEFAULT_LANGUAGE: str = "de"

    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProjectConfig:
    """Central configuration for the project."""

    _settings: ProjectSettings | None = None
    _logger: logging.Logger | None = None

    @classmethod
    def get_settings(cls) -> ProjectSettings:
        """Returns the project settings, initializing them if necessary."""
        if cls._settings is None:
            cls._settings = ProjectSettings()
        return cls._settings

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Returns the central logger, initializing it if necessary."""
        if cls._logger is None:
            # configure centralized logging if not already done
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            cls._logger = logging.getLogger("project")
            cls._logger.setLevel(cls.get_settings().LOG_LEVEL)
        return cls._logger
