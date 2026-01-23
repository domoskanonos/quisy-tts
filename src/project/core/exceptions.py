"""Domain exceptions for the TTS application."""


class TTSError(Exception):
    """Base exception for TTS-related errors."""

    pass


class EngineUnavailableError(TTSError):
    """Raised when the TTS engine is not available."""

    pass


class InvalidLanguageError(TTSError):
    """Raised when an unsupported language is requested."""

    pass


class AudioGenerationError(TTSError):
    """Raised when audio generation fails."""

    pass


class ReferenceAudioNotFoundError(TTSError):
    """Raised when reference audio file is not found."""

    pass
