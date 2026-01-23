"""Main entry point for the project."""

from project.config import ProjectConfig


def main() -> None:
    """Start the python blueprint."""
    logger = ProjectConfig.get_logger()
    settings = ProjectConfig.get_settings()

    logger.info(f"Starting {settings.PROJECT_NAME}...")
    logger.info("start python blueprint")


if __name__ == "__main__":
    main()
