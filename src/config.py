import logging
import os
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
import sqlite3


class ProjectSettings(BaseSettings):
    """Project settings using Pydantic."""

    # Example settings with default values
    # These can be overridden by environment variables (e.g. PROJECT_NAME)
    PROJECT_NAME: str = "quisy-tts"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8045

    # Base directory for all data
    # Resolved to absolute path at project root
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    BASE_DATA_DIR: Path = BASE_DIR / "data"

    # TTS Settings
    MODEL: str = "1.7"

    @property
    def DEFAULT_MODEL_SIZE(self) -> str:
        """Returns the model size (e.g., '1.7B') based on the configured model version."""
        if self.MODEL == "1.7":
            return "1.7B"
        elif self.MODEL == "0.6":
            return "0.6B"
        raise ValueError(f"Unsupported model version: {self.MODEL}")

    @property
    def MODELS_TO_DOWNLOAD(self) -> list[str]:
        """Returns the list of model IDs to download based on the configured model version."""
        if self.MODEL == "1.7":
            return [
                "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            ]
        elif self.MODEL == "0.6":
            return [
                "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
                "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            ]
        else:
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

    DEFAULT_LANGUAGE: str = "german"

    # When set, this should be a voice `id` existing in the SQLite voices
    # database (e.g. the seeded ids `german_audiobook_male_narrator_01`, ...). If provided, the
    # engine will prefer the audio file attached to that voice as the default
    # reference for voice cloning. If unset, the system will fall back to
    # selecting the first available `.wav` in `VOICES_DIR`.
    DEFAULT_VOICE_ID: str | None = None

    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class _RequiredEnv:
    """List of env vars that must be present (in environment or .env file).

    The project provides sensible defaults for many settings, but some
    directories and model lists are required to be explicitly configured
    in the runtime environment or the project's .env file. If any of the
    required variables is not present the program will exit with a clear
    error message to avoid silent misconfiguration.
    """

    VARS: list[str] = []


class ProjectConfig:
    """Central configuration for the project."""

    _settings: ProjectSettings | None = None
    _logger: logging.Logger | None = None

    @classmethod
    def get_settings(cls) -> ProjectSettings:
        """Returns the project settings, initializing them if necessary."""
        if cls._settings is None:
            # instantiate settings (this reads env + .env)
            cls._settings = ProjectSettings()

            # verify presence of required env vars either in the environment
            # or in the .env file referenced by the pydantic settings.
            missing: list[str] = []

            # collect keys from .env file if present
            env_file_path = ProjectSettings.model_config.get("env_file")
            env_file_path_str = str(env_file_path) if env_file_path is not None else None
            env_file_keys: set[str] = set()
            try:
                if env_file_path_str and Path(env_file_path_str).is_file():
                    with open(env_file_path_str, "r", encoding="utf-8") as fh:
                        for line in fh:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                k = line.split("=", 1)[0].strip()
                                if k:
                                    env_file_keys.add(k)
            except Exception:
                # don't crash reading the file; absence will be handled below
                env_file_keys = set()

            for key in _RequiredEnv.VARS:
                if key in os.environ or key in env_file_keys or getattr(cls._settings, key, None):
                    continue
                missing.append(key)

            if missing:
                sys.stderr.write("ERROR: Missing required environment variables: " + ", ".join(missing) + "\n")
                sys.stderr.write(
                    "Please add them to your environment or to the .env file at: " + str(env_file_path) + "\n"
                )
                # terminate instantly to avoid running with incomplete config
                raise SystemExit(1)

            # If a default voice ID is configured, validate it exists in the
            # application's SQLite voices database (we now use the resources DB
            # as the single authoritative, writable runtime database).
            assert cls._settings is not None
            try:
                # We know _settings is not None here
                settings = cls._settings
                default_voice_id = getattr(settings, "DEFAULT_VOICE_ID", None)
                if default_voice_id:
                    # We require the resources DB to be present and writable.
                    resource_db = Path(settings.RESOURCES_DIR) / "quisy-tts.db"
                    if not resource_db.exists():
                        sys.stderr.write(
                            f"ERROR: DEFAULT_VOICE_ID is set to '{default_voice_id}', but resources DB was not found at: {resource_db}\n"
                        )
                        raise SystemExit(1)

                    # Ensure we can write to the resources DB (append test)
                    try:
                        with open(resource_db, "ab"):
                            pass
                    except Exception as e:
                        sys.stderr.write(f"ERROR: resources DB '{resource_db}' is not writable: {e}\n")
                        raise SystemExit(1)

                    # Query DB for the voice id
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
                        raise SystemExit(1)
            except SystemExit:
                raise
            except Exception:
                # Be defensive: any unexpected error should prevent silent startup.
                sys.stderr.write("ERROR: Unexpected error while validating DEFAULT_VOICE_ID.\n")
                raise SystemExit(1)
        assert cls._settings is not None
        return cls._settings

    @classmethod
    def reset(cls) -> None:
        """Resets the configuration, forcing re-initialization on next get_settings()."""
        cls._settings = None
        cls._logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Returns the central logger, initializing it if necessary."""
        if cls._logger is None:
            # configure centralized logging if not already done
            logging.basicConfig(
                level=logging.INFO,
                format=("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s"),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            cls._logger = logging.getLogger("project")
            cls._logger.setLevel(cls.get_settings().LOG_LEVEL)
        return cls._logger
