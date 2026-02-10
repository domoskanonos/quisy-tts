"""Language mapping and resolution for TTS."""

# Map short language codes to full names expected by Qwen TTS
# Official Qwen3-TTS uses capitalized names: Chinese, English, German, etc.
LANGUAGE_MAP: dict[str, str] = {
    "de": "German",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "auto": "Auto",
    # Also support lowercase full names
    "german": "German",
    "english": "English",
    "french": "French",
    "spanish": "Spanish",
    "italian": "Italian",
    "portuguese": "Portuguese",
    "russian": "Russian",
    "japanese": "Japanese",
    "korean": "Korean",
    "chinese": "Chinese",
}


def resolve_language(lang: str) -> str:
    """Resolves a language code to the full name expected by Qwen TTS."""
    return LANGUAGE_MAP.get(lang, lang)
