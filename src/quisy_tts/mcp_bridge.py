import os
import uuid
import asyncio
from fastmcp import FastMCP
from quisy_tts.client import QuisyTTS
from quisy_tts.schemas import TTSParams
from quisy_tts.audio.processor import AudioProcessor

# Initialize the MCP server
mcp = FastMCP("QuisyTTS-Server")
client = QuisyTTS()

# Semaphore to ensure only one heavy task runs at a time
generation_semaphore = asyncio.Semaphore(1)

tts_service = client.tts_service
voice_service = client.voice_service
settings = client.settings


@mcp.tool
async def search_voices(q: str | None = None, terms: str | None = None, limit: int = 20, offset: int = 0) -> str:
    """Search for available voices."""
    term_list = [t.strip() for t in terms.split(",")] if terms else []
    results = voice_service.search(term_list, q, limit=limit, offset=offset)
    return str(results)


@mcp.tool
async def get_voice_details(voice_id: str) -> str:
    """Retrieve detailed metadata for a specific voice."""
    voice = voice_service.get_voice(voice_id)
    if not voice:
        return f"Error: Voice '{voice_id}' not found."
    return str(voice)


@mcp.tool
async def generate_voice(text: str, voice_id: str, language: str = "german", instruct: str | None = None) -> str:
    """Generate audio from text using a specific voice."""
    async with generation_semaphore:
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
        return str(result_path)


@mcp.tool
async def generate_ssml(ssml_content: str) -> str:
    """Generate audio from SSML markup."""
    async with generation_semaphore:
        base_params = TTSParams(mode="base", model_size="1.7B")
        result_path = await tts_service.generate_from_ssml(ssml_content, base_params)
        return str(result_path)


@mcp.tool
async def concatenate_audio(audio_files: list[str]) -> str:
    """Concatenate multiple audio files into a single WAV file."""
    async with generation_semaphore:
        input_paths = []
        for f in audio_files:
            p_out = settings.AUDIO_DIR / f
            if p_out.exists():
                input_paths.append(str(p_out))
            else:
                return f"Error: File '{f}' not found."

        output_filename = f"concat_{uuid.uuid4()}.wav"
        output_path = os.path.join(settings.AUDIO_DIR, output_filename)
        if not AudioProcessor.concatenate_audio(input_paths, output_path):
            return "Error: Concatenation failed."
        return str(output_path)


def main():
    """Main entry point for the MCP server script."""
    mcp.run()


if __name__ == "__main__":
    main()
