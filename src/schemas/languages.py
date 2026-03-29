"""Language mapping and resolution for TTS."""

# Map language codes/names to lowercase names expected by qwen-tts
LANGUAGE_MAP: dict[str, str] = {
    # ISO codes mapping to qwen-tts expected names
    "de": "german",
    "en": "english",
    "fr": "french",
    "es": "spanish",
    "it": "italian",
    "pt": "portuguese",
    "ru": "russian",
    "ja": "japanese",
    "ko": "korean",
    "zh": "chinese",
    # Also support direct names
    "german": "german",
    "english": "english",
    "french": "french",
    "spanish": "spanish",
    "italian": "italian",
    "portuguese": "portuguese",
    "russian": "russian",
    "japanese": "japanese",
    "korean": "korean",
    "chinese": "chinese",
}


def resolve_language(lang: str) -> str:
    """Resolves a language code or name to the lowercase name expected by qwen-tts."""
    return LANGUAGE_MAP.get(lang.lower(), lang.lower())
