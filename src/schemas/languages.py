"""Language mapping and resolution for TTS."""

# Map language codes/names to lowercase names expected by qwen-tts
# qwen-tts expects: auto, chinese, english, french, german, italian,
#                    japanese, korean, portuguese, russian, spanish
LANGUAGE_MAP: dict[str, str] = {
    # ISO codes
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
    "auto": "auto",
    # English names (case-insensitive via .lower())
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
    # Native language names
    "deutsch": "german",
    "englisch": "english",
    "französisch": "french",
    "spanisch": "spanish",
    "italienisch": "italian",
    "portugiesisch": "portuguese",
    "russisch": "russian",
    "japanisch": "japanese",
    "koreanisch": "korean",
    "chinesisch": "chinese",
}


def resolve_language(lang: str) -> str:
    """Resolves a language code or name to the lowercase name expected by qwen-tts."""
    return LANGUAGE_MAP.get(lang.lower(), lang.lower())
