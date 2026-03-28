from fastmcp import FastMCP
from schemas import TTSParams
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
async def search_voices(q: str | None = None, terms: str | None = None, limit: int = 20, offset: int = 0) -> str:
    """Search voices by free text query and optional comma-separated terms."""
    term_list = [t.strip() for t in terms.split(",")] if terms else []
    results = voice_service.search(term_list, q, limit=limit, offset=offset)
    return str(results)


@mcp.tool
async def get_voice_details(voice_id: str) -> str:
    """Get detailed information about a specific voice."""
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."
    return str(voice)


@mcp.tool
async def create_voice(name: str, example_text: str, instruct: str, language: str = "German") -> str:
    """Create a new voice metadata entry."""
    voice = voice_service.create_voice(
        name=name,
        example_text=example_text,
        instruct=instruct,
        language=language,
    )
    if not voice:
        return "Error: Failed to create voice."
    return str(voice)


@mcp.tool
async def delete_voice(voice_id: str) -> str:
    """Delete a voice and its associated audio file."""
    if not voice_service.delete_voice(voice_id):
        return f"Error: Failed to delete voice '{voice_id}'."
    return f"Voice '{voice_id}' deleted successfully."


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
    text: str, voice_id: str, language: str = "German", instruct: str | None = None
) -> str:
    """
    Generate audio using a specific voice_id with the 0.6B model.
    """
    if not voice_service.get_voice(voice_id):
        return f"Error: Voice '{voice_id}' not found."

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="custom_voice",
        model_size="0.6B",
        speaker=voice_id,
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_custom_voice_17b(
    text: str, voice_id: str, language: str = "German", instruct: str | None = None
) -> str:
    """
    Generate audio using a specific voice_id with the 1.7B model.
    """
    if not voice_service.get_voice(voice_id):
        return f"Error: Voice '{voice_id}' not found."

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="custom_voice",
        model_size="1.7B",
        speaker=voice_id,
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_ssml(ssml_content: str) -> str:
    """
    Generates audio from SSML markup with strict validation.

    Rules:
    - Root: <speak>...</speak>
    - Text: <speaker name="VoiceID">Text</speaker>
    - Break (Time): <break time="250ms" /> or <break time="1.5s" />
    - Break (Strength): <break strength="medium" />
    - Invalid XML or missing voices will cause an immediate error.

    Example:
    <speak>
        <speaker name="eric">Hallo!</speaker>
        <break time="500ms" />
        <speaker name="Chelsie">Wie geht es dir?</speaker>
    </speak>
    """
    base_params = TTSParams(mode="custom_voice", model_size="1.7B")
    result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
    return get_audio_url(str(result_path))
