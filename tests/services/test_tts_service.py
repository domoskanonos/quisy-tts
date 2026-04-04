import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from services.tts_service import TTSService
import services.tts.generator


@pytest.mark.asyncio
async def test_tts_service_initialization():
    # Mock dependencies
    engine = MagicMock()
    cache = MagicMock()
    voice_service = MagicMock()
    ssml_processor = MagicMock()
    voice_audio_integrity = MagicMock()
    logger = MagicMock()

    service = TTSService(
        engine=engine,
        cache=cache,
        voice_service=voice_service,
        ssml_processor=ssml_processor,
        voice_audio_integrity=voice_audio_integrity,
        logger=logger,
    )

    assert service.engine == engine
    assert service.cache == cache
    assert service.voice_service == voice_service
    assert service.ssml_processor == ssml_processor
    assert service.voice_audio_integrity == voice_audio_integrity
    assert service.logger == logger


@pytest.mark.asyncio
async def test_generate_audio_calls_generator():
    # Setup
    engine = MagicMock()
    cache = MagicMock()
    voice_service = MagicMock()
    ssml_processor = MagicMock()
    voice_audio_integrity = MagicMock()
    logger = MagicMock()

    service = TTSService(
        engine=engine,
        cache=cache,
        voice_service=voice_service,
        ssml_processor=ssml_processor,
        voice_audio_integrity=voice_audio_integrity,
        logger=logger,
    )

    # We need to mock the generator module function

    services.tts.generator.generate_audio = AsyncMock(return_value=Path("test.wav"))

    result = await service.generate_audio(text="hello", language="en")

    assert result == Path("test.wav")
