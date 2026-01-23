import pytest

from project.config import ProjectConfig
from project.main import main


def test_main_execution() -> None:
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised {e} unexpectedly!")


def test_settings_load() -> None:
    settings = ProjectConfig.get_settings()
    assert settings.PROJECT_NAME is not None


def test_logger_initialization() -> None:
    logger = ProjectConfig.get_logger()
    assert logger.name == "project"
