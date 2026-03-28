from fastmcp import FastMCP
from api.dependencies import get_tts_service, get_voice_service
from config import ProjectConfig
import os

# Initialize MCP server
mcp = FastMCP("QuisyTTS-MCP-Server")

# Services
tts_service = get_tts_service()
voice_service = get_voice_service()
settings = ProjectConfig.get_settings()

# Base URL for audio files
base_audio_url = f"http://localhost:{settings.PORT}/audio"


def get_audio_url(file_path: str) -> str:
    """Converts a local file path to an accessible URL."""
    filename = os.path.basename(file_path)
    return f"{base_audio_url}/{filename}"


@mcp.tool
async def generate_base_06b(
    text: str, language: str = "German", reference_audio: str | None = None, ref_text: str | None = None
) -> str:
    """
    Generates audio using base mode (voice cloning) with the 0.6B model.

    Args:
        text: The text to be converted to speech.
        language: The language (e.g., 'German', 'English').
        reference_audio: Optional voice ID to clone.
        ref_text: Optional transcript of the reference audio for better quality.
    """
    if reference_audio and voice_service.get_voice(reference_audio) is None:
        return f"Error: Reference voice id '{reference_audio}' not found"

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="base",
        model_size="0.6B",
        reference_audio=reference_audio,
        ref_text=ref_text,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_base_17b(
    text: str, language: str = "German", reference_audio: str | None = None, ref_text: str | None = None
) -> str:
    """
    Generates audio using base mode (voice cloning) with the 1.7B model.

    Args:
        text: The text to be converted to speech.
        language: The language (e.g., 'German', 'English').
        reference_audio: Optional voice ID to clone.
        ref_text: Optional transcript of the reference audio for better quality.
    """
    if reference_audio and voice_service.get_voice(reference_audio) is None:
        return f"Error: Reference voice id '{reference_audio}' not found"

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="base",
        model_size="1.7B",
        reference_audio=reference_audio,
        ref_text=ref_text,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_voice_design_17b(text: str, instruct: str, language: str = "German") -> str:
    """
    Generate audio using voice design mode with the 1.7B model.

    Args:
        text: The text to be converted to speech.
        instruct: A natural language description of the voice (e.g., 'A deep, calm male voice').
        language: The language.
    """
    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="voice_design",
        model_size="1.7B",
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_custom_voice_06b(
    text: str, speaker: str, language: str = "German", instruct: str | None = None
) -> str:
    """
    Generate audio using a specific speaker with the 0.6B model.

    Args:
        text: The text to be converted to speech.
        speaker: The name of the speaker (use list_voices to find valid names).
        language: The language.
        instruct: Optional style instruction (e.g., 'happy', 'whispering').
    """
    voice = voice_service.get_voice_by_name(speaker)
    if not voice:
        return f"Error: Speaker '{speaker}' not found in database."

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="custom_voice",
        model_size="0.6B",
        speaker=voice["id"],
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_custom_voice_17b(
    text: str, speaker: str, language: str = "German", instruct: str | None = None
) -> str:
    """
    Generate audio using a specific speaker with the 1.7B model.

    Args:
        text: The text to be converted to speech.
        speaker: The name of the speaker (use list_voices to find valid names).
        language: The language.
        instruct: Optional style instruction (e.g., 'happy', 'whispering').
    """
    voice = voice_service.get_voice_by_name(speaker)
    if not voice:
        return f"Error: Speaker '{speaker}' not found in database."

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="custom_voice",
        model_size="1.7B",
        speaker=voice["id"],
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def list_voices() -> str:
    """Lists all available voices and their IDs for use in custom or base modes."""
    voices = voice_service.list_voices()
    return str(voices)
