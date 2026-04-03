import os
import uuid
import httpx
from fastmcp import FastMCP
from schemas import TTSParams
from api.dependencies import get_tts_service, get_voice_service
from config import ProjectConfig
from audio.processor import AudioProcessor

# Initialize MCP server
mcp = FastMCP("QuisyTTS-Voice-Engine")

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
    """
    Search for available voices based on a free text query and optional comma-separated terms.

    - q: Optional free text search query.
    - terms: Optional comma-separated search terms for filtering (e.g., 'male,narrator,calm').
    - limit: Maximum number of results to return (default 20).
    - offset: Pagination offset (default 0).

    Returns a string representation of the matching voices.
    """
    term_list = [t.strip() for t in terms.split(",")] if terms else []
    results = voice_service.search(term_list, q, limit=limit, offset=offset)
    return str(results)


@mcp.tool
async def get_voice_details(voice_id: str) -> str:
    """
    Retrieve detailed metadata for a specific voice by its ID.

    - voice_id: The unique identifier of the voice.

    Returns a string representation of the voice details or an error message if not found.
    """
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."
    return str(voice)


@mcp.tool
async def create_voice(name: str, example_text: str, instruct: str, language: str = "german") -> str:
    """
    Create a new voice metadata entry and queue generation of its reference audio.

    - name: Unique voice identifier (DB id).
    - example_text: Short example sentence used to generate the reference audio.
    - instruct: Natural language description for the voice style (e.g., 'warm, professional').
    - language: Target language (e.g., 'german', 'english').

    Returns a string representation of the created voice metadata or an error message.
    """
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
async def generate_voice(text: str, voice_id: str, language: str = "german", instruct: str | None = None) -> str:
    """
    Generate audio from text using a specific voice via base mode (voice cloning).

    - text: The text to convert to speech.
    - voice_id: The ID of an existing, registered voice.
    - language: Target language (e.g., 'german', 'english').
    - instruct: Optional style instructions in English (e.g., 'speak softly').

    Returns the public URL to the generated audio file, or an error message if generation fails.
    """
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."

    # Ensure reference audio exists before generation
    print(f"DEBUG: Ensuring audio for voice {voice_id}")
    await tts_service.voice_audio_integrity.ensure_audio(voice_id, tts_service.generate_audio)
    print(f"DEBUG: Audio ensured for voice {voice_id}")

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
    Upload a local WAV file to the server for use in subsequent operations.

    - local_path: Absolute path to the local .wav file.

    Returns the filename of the uploaded file on the server, or an error message.
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
    Generate audio from SSML markup.

    Rules:
    - Root element must be `<speak>`.
    - Spoken text must be wrapped in `<speaker name="VoiceID">...</speaker>`.
    - `<break>` and `<sfx>` tags are supported.
    - Speaker language is derived from voice settings.

    Returns the public URL to the generated audio file.
    """
    base_params = TTSParams(mode="base", model_size="1.7B")
    result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
    return get_audio_url(str(result_path))


@mcp.tool
async def concatenate_audio(audio_files: list[str]) -> str:
    """
    Concatenate multiple audio files into a single WAV file.

    - audio_files: A list of filenames existing in the server's audio or upload directories.

    Returns the public URL to the concatenated audio file, or an error message.
    """
    # Search for files in AUDIO_DIR and UPLOAD_DIR
    input_paths = []
    for f in audio_files:
        p_out = settings.AUDIO_DIR / f
        p_up = settings.UPLOAD_DIR / f

        if p_out.exists():
            input_paths.append(str(p_out))
        elif p_up.exists():
            input_paths.append(str(p_up))
        else:
            return f"Error: File '{f}' not found in output or upload directories."

    output_filename = f"concat_{uuid.uuid4()}.wav"
    output_path = os.path.join(settings.AUDIO_DIR, output_filename)

    if not AudioProcessor.concatenate_audio(input_paths, output_path):
        return "Error: Concatenation failed."

    return get_audio_url(output_path)
