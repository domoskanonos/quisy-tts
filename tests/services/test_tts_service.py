import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from services.tts_service import TTSService
import services.tts.generator


@pytest.mark.asyncio
async def test_tts_service_concurrency_locking():
    # Setup
    cache = MagicMock()
    # Mock get_lock to return a real asyncio.Lock instance
    cache.get_lock = lambda key: asyncio.Lock()

    # Initialize service
    service = TTSService(
        engine=MagicMock(),
        cache=cache,
        voice_service=MagicMock(),
        ssml_processor=MagicMock(),
        voice_audio_integrity=MagicMock(),
        audio_converter=MagicMock(),
        logger=MagicMock(),
    )

    key = "test_key"

    # Assert that getting a lock for the same key twice returns the SAME lock object
    lock1 = service._get_lock(key)
    lock2 = service._get_lock(key)

    # We should NOT use the mock `get_lock` which returns a new instance every time,
    # but rather test the default behavior (the internal dictionary)

    # Let's re-run the test without mocking get_lock to test the internal _locks dict
    cache = MagicMock()
    # Ensure it doesn't return anything callable
    cache.get_lock = None

    service = TTSService(
        engine=MagicMock(),
        cache=cache,
        voice_service=MagicMock(),
        ssml_processor=MagicMock(),
        voice_audio_integrity=MagicMock(),
        audio_converter=MagicMock(),
        logger=MagicMock(),
    )

    lock1 = service._get_lock(key)
    lock2 = service._get_lock(key)

    assert lock1 is lock2
    assert isinstance(lock1, asyncio.Lock)

    # Verify lock functionality: ensure we can acquire/release
    async with lock1:
        assert lock1.locked()
    assert not lock1.locked()


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
        audio_converter=MagicMock(),
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
        audio_converter=MagicMock(),
        logger=logger,
    )

    # We need to mock the generator module function

    services.tts.generator.generate_audio = AsyncMock(return_value=Path("test.wav"))

    result = await service.generate_audio(text="hello", language="english")

    assert result == Path("test.wav")
