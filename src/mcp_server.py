import os
import uuid
from fastmcp import FastMCP
from schemas import TTSParams
from api.dependencies import get_tts_service, get_voice_service, get_voice_audio_integrity
from config import ProjectConfig
from audio.processor import AudioProcessor

# Initialize MCP server
mcp = FastMCP("QuisyTTS-Voice-Engine")

# Services
tts_service = get_tts_service()
voice_service = get_voice_service()
voice_audio_integrity_service = get_voice_audio_integrity()
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
    Search for available voices in the QuisyTTS database.
    This tool is essential for finding the correct 'voice_id' before generating audio.

    Args:
        q: Optional free text search query. Searches through voice names, descriptions, and example texts.
        terms: Optional comma-separated list of style terms to filter by (e.g., 'male,narrator,calm,professional').
        limit: Maximum number of voices to return (default 20, max 200).
        offset: Pagination offset for browsing large result sets.

    Returns:
        A JSON-formatted string containing a list of matching voice objects (metadata like voice_id, name, instruct, language).
    """
    term_list = [t.strip() for t in terms.split(",")] if terms else []
    results = voice_service.search(term_list, q, limit=limit, offset=offset)
    return str(results)


@mcp.tool
async def get_voice_details(voice_id: str) -> str:
    """
    Retrieve full metadata for a specific voice.
    Use this to understand a voice's style (instruct) or language before using it for generation.

    Args:
        voice_id: The unique identifier of the voice (e.g., 'german_audiobook_female_narrator_01').

    Returns:
        A JSON-formatted string of the voice details or an error message if the ID is invalid.
    """
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."
    return str(voice)


@mcp.tool
async def create_voice(name: str, example_text: str, instruct: str, language: str = "german") -> str:
    """
    Create a completely new custom voice (Voice Design).
    This tool triggers the Qwen-TTS 1.7B VoiceDesign model to 'dream' up a new voice based on your description.

    Args:
        name: A unique, descriptive name/ID for the new voice (e.g., 'mysterious_storyteller').
        example_text: A short sentence that the new voice will speak to generate its initial reference audio.
        instruct: A detailed natural language description of the voice style (e.g., 'A raspy, old male voice with a mysterious and slow-paced tone').
        language: The target language of the voice. Use full names like 'german', 'english', etc.

    Returns:
        A JSON string of the newly created voice metadata. The voice is immediately ready for use in 'generate_voice'.
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
    Convert text to speech using an existing voice (Voice Cloning / Zero-shot TTS).
    This is the primary tool for high-quality audio generation.

    Args:
        text: The text to be spoken. Keep it under 500 characters for optimal performance.
        voice_id: The ID of the voice to use (find IDs via 'search_voices').
        language: The language of the text. Must match the voice's capabilities. Use full names (e.g., 'german').
        instruct: Optional. Overwrite or refine the voice's style. If omitted, the 'instruct' (style description)
                  from the voice's database entry is used automatically.

    Returns:
        A public URL to the generated WAV audio file.
    """
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."

    # Use instruct from DB if not provided via tool call
    final_instruct = instruct or voice.get("instruct")

    # Ensure reference audio exists before generation
    await voice_audio_integrity_service.ensure_audio(voice_id, generator_callback=tts_service.generate_audio)

    result_path = await tts_service.generate_audio(
        text=text,
        language=language,
        mode="base",
        model_size="1.7B",
        reference_audio=voice_id,
        ref_text=voice.get("example_text"),
        instruct=final_instruct,
    )
    return get_audio_url(str(result_path))


@mcp.tool
async def generate_ssml(ssml_content: str) -> str:
    """
    Generate complex audio using SSML (Speech Synthesis Markup Language).
    Use this for multi-speaker dialogs, precise timing, or emotional control.

    Required Format:
    - Root: `<speak>...</speak>`
    - Speaker: Wrap text in `<speaker name="VoiceID">...</speaker>`
    - Pauses: Use `<break time="500ms"/>` or `<break time="1.5s"/>`

    Example:
    <speak>
      <speaker name="voice_a">Hello!</speaker>
      <break time="1s"/>
      <speaker name="voice_b">Hi there, how are you?</speaker>
    </speak>

    Args:
        ssml_content: The full SSML markup string.

    Returns:
        A public URL to the resulting multi-speaker WAV file.
    """
    base_params = TTSParams(mode="base", model_size="1.7B")
    result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
    return get_audio_url(str(result_path))


@mcp.tool
async def concatenate_audio(audio_files: list[str]) -> str:
    """
    Merge multiple existing audio files into one single long WAV file.
    Useful for combining several generated sentences or adding intros/outros.

    Args:
        audio_files: A list of filenames (e.g., ['file1.wav', 'file2.wav']) that already exist on the server (either generated or uploaded).

    Returns:
        A public URL to the final concatenated WAV file.
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
