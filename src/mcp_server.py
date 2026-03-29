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
async def create_voice(name: str, example_text: str, instruct: str, language: str = "de") -> str:
    """
    Create a new voice metadata entry.

    - name: Unique voice identifier (DB id).
    - example_text: Short example sentence used to generate the reference audio.
    - instruct: Natural language description for voice design (style).
    - language: Target language for the reference audio. This must be provided by the caller
      and is not inferred by the service. Allowed values: short codes 'de','en','fr','es','it','pt','ru','ja','ko','zh'
      or the full names 'german','english', etc. A missing language will cause generation to fail.

    The created voice will be stored in the voices DB and its reference audio should be generated
    (the application will attempt to generate it on demand or at startup).
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
async def generate_voice(text: str, voice_id: str, language: str = "de", instruct: str | None = None) -> str:
    """
    Generate audio using a specific voice_id (DB) with base mode (voice cloning).

    Parameters
    - text: The text to convert to speech.
    - voice_id: The ID of an existing voice in the DB (must exist).
    - language: Required target language for synthesis. Provide either short codes
      ('de','en','fr','es','it','pt','ru','ja','ko','zh') or full names ('german','english', ...).
      The service will raise an error if language is missing or unknown.
    - instruct: Optional style instruction. For best cross-language behavior provide
      style hints in English (e.g. 'speak like a professional newscaster').

    Returns a publicly accessible URL to the generated audio file on success or an
    error string on failure.
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
    Uploads a local WAV file to the server and returns the stored filename.

    - local_path: Absolute path to the local .wav file to upload.

    The upload endpoint validates the file exists and forwards it to the HTTP
    upload API. Only valid audio files are accepted by the API endpoint.
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

    Expectations & rules
    - The SSML root element must be <speak>.
    - All spoken text must be wrapped in <speaker name="VoiceID">...</speaker> elements.
      The referenced VoiceID must exist in the voices DB and have a language attribute set.
    - <break> supports either a time attribute (e.g. '250ms' or '1.5s') or a strength
      attribute ('none','x-weak','weak','medium','strong','x-strong').
    - <sfx> (sound effect) tags may be used and will trigger the audio SFX service.

    Language handling
    - The language for each speaker is taken from the corresponding voice DB entry.
      The SSML payload does not need a global language field when speakers carry
      language information, but every referenced voice must include a non-empty
      language value (short code or full name). If a referenced voice lacks a
      language the generation will fail.

    Returns a public URL to the generated audio file on success.
    """
    base_params = TTSParams(mode="base", model_size="1.7B")
    result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
    return get_audio_url(str(result_path))


@mcp.tool
async def concatenate_audio(audio_files: list[str]) -> str:
    """Concatenate multiple audio files into one and return the URL."""
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

    if not SoxAudioProcessor.concatenate_audio(input_paths, output_path):
        return "Error: Concatenation failed."

    return get_audio_url(output_path)
