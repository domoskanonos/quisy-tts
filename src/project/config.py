import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """Project settings using Pydantic."""

    # Example settings with default values
    # These can be overridden by environment variables (e.g. PROJECT_NAME)
    PROJECT_NAME: str = "python-starter"
    LOG_LEVEL: str = "INFO"

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
