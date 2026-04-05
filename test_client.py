from src.quisy_tts import QuisyTTS
import asyncio


async def test():
    tts = QuisyTTS()
    print("QuisyTTS initialized successfully.")

    # Simple check for voice service availability
    voices = tts.voice_service.list_voices()
    print(f"Voices found: {len(voices)}")


if __name__ == "__main__":
    asyncio.run(test())
