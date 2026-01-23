import re


class NaturalOptimizer:
    """Handles text cleaning and optimization for natural speech."""

    def optimize(self, text: str) -> str:
        """Cleans and optimizes text for TTS."""
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text
