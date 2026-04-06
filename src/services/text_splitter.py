"""Simple text splitting service.

Does NOT split text automatically. Text is returned as a single chunk.
"""

from config import ProjectConfig

logger = ProjectConfig.get_logger()


class TextSplitterService:
    """Returns text as a single chunk."""

    def __init__(self, max_chunk_chars: int = 0) -> None:
        self.max_chunk_chars = max_chunk_chars

    def split(self, text: str, language: str = "german") -> list[str]:
        """Returns the full text as a single chunk.

        Args:
            text: The full input text.
            language: The resolved language name (e.g. 'german', 'english').

        Returns:
            A list containing the full text as one chunk if not empty.
        """
        text = text.strip()
        if not text:
            return []

        logger.debug(f"TextSplitter: Returning full text for '{language}'.")
        return [text]


# Module-level singleton for convenience
_splitter: TextSplitterService | None = None


def get_text_splitter(max_chunk_chars: int = 0) -> TextSplitterService:
    """Get or create the singleton TextSplitterService."""
    global _splitter
    if _splitter is None or _splitter.max_chunk_chars != max_chunk_chars:
        _splitter = TextSplitterService(max_chunk_chars)
    return _splitter
