import os
import uuid
import httpx
from fastmcp import FastMCP
from schemas import TTSParams
from api.dependencies import get_tts_service, get_voice_service
from config import ProjectConfig
from audio.processor import SoxAudioProcessor

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
async def generate_voice(text: str, voice_id: str, language: str = "German", instruct: str | None = None) -> str:
    """
    Generate audio using a specific voice_id (DB) with base mode (1.7B).

    Args:
        text: The text to convert to speech.
        voice_id: The ID of the voice to use.
        language: The target language (e.g., 'German').
        instruct: Style instruction for the voice. NOTE: Instructions should be provided in English
                  for best results, regardless of the target voice's language.
    """
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="base",
        model_size="1.7B",
        reference_audio=voice_id,
        ref_text=voice.get("example_text"),
        instruct=instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def upload_audio(local_path: str) -> str:
    """
    Uploads a local audio file to the server.

    Args:
        local_path: The absolute path to the local .wav file to upload.

    Returns:
        The filename of the uploaded file on the server.
    """
    if not os.path.exists(local_path):
        return f"Error: File '{local_path}' not found."

    url = f"http://localhost:{settings.PORT}/api/audio/upload"
    async with httpx.AsyncClient() as client:
        with open(local_path, "rb") as f:
            files = {"file": (os.path.basename(local_path), f, "audio/wav")}
            response = await client.post(url, files=files)

    if response.status_code != 200:
        return f"Error: Upload failed with status {response.status_code}: {response.text}"

    return response.json()["filename"]


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
    base_params = TTSParams(mode="base", model_size="1.7B")
    result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
    return get_audio_url(str(result_path))


@mcp.tool
async def concatenate_audio(audio_files: list[str]) -> str:
    """Concatenate multiple audio files into one and return the URL."""
    # Search for files in OUTPUT_DIR and UPLOAD_DIR
    input_paths = []
    for f in audio_files:
        p_out = settings.OUTPUT_DIR / f
        p_up = settings.UPLOAD_DIR / f

        if p_out.exists():
            input_paths.append(str(p_out))
        elif p_up.exists():
            input_paths.append(str(p_up))
        else:
            return f"Error: File '{f}' not found in output or upload directories."

    output_filename = f"concat_{uuid.uuid4()}.wav"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

    if not SoxAudioProcessor.concatenate_audio(input_paths, output_path):
        return "Error: Concatenation failed."

    return get_audio_url(output_path)
