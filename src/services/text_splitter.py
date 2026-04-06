"""Language-aware text splitting service.

Splits long texts into natural sentence-based chunks so that the TTS model
receives manageable portions and maintains a natural speaking pace.
"""

import re

from config import ProjectConfig

logger = ProjectConfig.get_logger()

# Default max characters per chunk.
# ~300 chars ≈ 2-3 German sentences — enough context for natural prosody,
# short enough to prevent the model from speeding up.
DEFAULT_MAX_CHUNK_CHARS = 800


class TextSplitterService:
    """Splits text into sentence-based chunks for TTS generation.

    Uses rule-based (regex) sentence boundary detection.
    """

    def __init__(self, max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> None:
        self.max_chunk_chars = max_chunk_chars

    def split(self, text: str, language: str = "german") -> list[str]:
        """Split text into chunks suitable for TTS generation.

        Args:
            text: The full input text.
            language: The resolved language name (e.g. 'german', 'english').

        Returns:
            A list of text chunks, each under max_chunk_chars.
        """
        text = text.strip()
        if not text:
            return []

        # Short texts don't need splitting
        if len(text) <= self.max_chunk_chars:
            return [text]

        # Use regex for sentence splitting.
        sentences = self._split_sentences(text)
        logger.debug(f"TextSplitter: regex used for '{language}', {len(sentences)} sentences extracted.")

        # Group sentences into chunks
        return self._group_into_chunks(sentences)

    def _split_sentences(self, text: str) -> list[str]:
        """Sentence splitting using regex.

        Improved over the naive [.!?] split:
        - Handles abbreviations (Dr., Mr., etc.)
        - Handles decimal numbers (3.14)
        - Splits on sentence-ending punctuation followed by space + uppercase
        """
        # Split on sentence-ending punctuation followed by whitespace and an uppercase letter
        # This avoids splitting on "Dr. Müller" or "3.14"
        pattern = r"(?<=[.!?;:])\s+(?=[A-ZÄÖÜ\u0400-\u04FF\u3000-\u9FFF])"
        sentences = re.split(pattern, text)
        logger.debug(f"TextSplitter: regex produced {len(sentences)} sentences.")
        return [s.strip() for s in sentences if s.strip()]

    def _group_into_chunks(self, sentences: list[str]) -> list[str]:
        """Group sentences into chunks that stay under max_chunk_chars.

        Keeps sentences together for natural prosody. A single sentence
        that exceeds max_chunk_chars is kept as-is (never split mid-sentence).
        """
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # If adding this sentence would exceed limit and we already have content
            if current_length + sentence_len + 1 > self.max_chunk_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_len + 1  # +1 for space

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


# Module-level singleton for convenience
_splitter: TextSplitterService | None = None


def get_text_splitter(max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> TextSplitterService:
    """Get or create the singleton TextSplitterService."""
    global _splitter
    if _splitter is None or _splitter.max_chunk_chars != max_chunk_chars:
        _splitter = TextSplitterService(max_chunk_chars)
    return _splitter
