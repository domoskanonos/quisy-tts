"""Language-aware text splitting service using spaCy.

Splits long texts into natural sentence-based chunks so that the TTS model
receives manageable portions and maintains a natural speaking pace.
"""

import re
import subprocess
import sys
from typing import Any, Optional

from config import ProjectConfig

logger = ProjectConfig.get_logger()

# Map resolved language names (lowercase, as used by qwen-tts) to spaCy model names
LANGUAGE_TO_SPACY_MODEL: dict[str, str] = {
    "german": "de_core_news_sm",
    "english": "en_core_web_sm",
    "french": "fr_core_news_sm",
    "spanish": "es_core_news_sm",
    "italian": "it_core_news_sm",
    "portuguese": "pt_core_news_sm",
    "russian": "ru_core_news_sm",
    "japanese": "ja_core_news_sm",
    "chinese": "zh_core_web_sm",
    "korean": "ko_core_news_sm",
}

# Default max characters per chunk.
# ~300 chars ≈ 2-3 German sentences — enough context for natural prosody,
# short enough to prevent the model from speeding up.
DEFAULT_MAX_CHUNK_CHARS = 300


class TextSplitterService:
    """Splits text into sentence-based chunks for TTS generation.

    Uses spaCy sentencizer (rule-based, fast) for accurate sentence boundary
    detection. Falls back to regex if no spaCy model is available.
    """

    def __init__(self, max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> None:
        self.max_chunk_chars = max_chunk_chars
        self._nlp_cache: dict[str, Optional[Any]] = {}

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

        # Use spaCy for sentence splitting. If spaCy model is not available for
        # the requested language, fail early — do not fall back to regex.
        sentences = self._split_sentences_spacy(text, language)
        if sentences is None:
            raise RuntimeError(f"No sentence splitter available for language '{language}'.")
        logger.debug(f"TextSplitter: spaCy used for '{language}', {len(sentences)} sentences extracted.")

        # Group sentences into chunks
        return self._group_into_chunks(sentences)

    def _split_sentences_spacy(self, text: str, language: str) -> list[str] | None:
        """Split text into sentences using spaCy.

        Returns None if the spaCy model is not available, signaling the caller
        to fall back to regex.
        """
        nlp = self._get_nlp(language)
        if nlp is None:
            return None

        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        return sentences if sentences else None

    def _get_nlp(self, language: str) -> Optional[Any]:
        """Get or load a spaCy NLP pipeline for the given language."""
        language = language.lower()

        if language in self._nlp_cache:
            return self._nlp_cache[language]

        model_name = LANGUAGE_TO_SPACY_MODEL.get(language)
        if not model_name:
            logger.debug(f"No spaCy model mapped for language '{language}', using regex fallback.")
            return None

        try:
            import spacy

            # Try loading the model
            try:
                nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "attribute_ruler"])
            except OSError:
                # Model not installed — try downloading it using the CLI to avoid
                # relying on spacy.cli.download (which can be missing in some
                # typing stubs). Using subprocess ensures the download step is
                # executed in a separate process.
                logger.info(f"spaCy model '{model_name}' not found. Downloading...")
                try:
                    subprocess.run([sys.executable, "-m", "spacy", "download", model_name], check=True)
                    nlp = spacy.load(model_name, disable=["ner", "lemmatizer", "attribute_ruler"])
                except Exception as dl_e:
                    logger.warning(f"Failed to download spaCy model '{model_name}': {dl_e}. Using regex fallback.")
                    self._nlp_cache[language] = None
                    return None

            # Ensure sentencizer is available (the parser handles this in sm models,
            # but we add a rule-based sentencizer as fallback if parser is disabled)
            if not nlp.has_pipe("sentencizer") and not nlp.has_pipe("parser"):
                nlp.add_pipe("sentencizer")

            self._nlp_cache[language] = nlp
            logger.info(f"spaCy model '{model_name}' loaded for language '{language}'.")
            return nlp

        except Exception as e:
            logger.warning(f"Failed to load spaCy model '{model_name}': {e}. Using regex fallback.")
            self._nlp_cache[language] = None
            return None

    def _split_sentences_regex(self, text: str) -> list[str]:
        """Fallback regex-based sentence splitting.

        Improved over the naive [.!?] split:
        - Handles abbreviations (Dr., Mr., etc.)
        - Handles decimal numbers (3.14)
        - Splits on sentence-ending punctuation followed by space + uppercase
        """
        # Split on sentence-ending punctuation followed by whitespace and an uppercase letter
        # This avoids splitting on "Dr. Müller" or "3.14"
        pattern = r"(?<=[.!?;:])\s+(?=[A-ZÄÖÜ\u0400-\u04FF\u3000-\u9FFF])"
        sentences = re.split(pattern, text)
        logger.debug(f"TextSplitter: regex fallback produced {len(sentences)} sentences.")
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
