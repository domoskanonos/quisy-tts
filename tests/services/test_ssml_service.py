import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch
from src.services.orchestrator.ssml import _process_task
from services.ssml_processor import TextTask, BreakTask
from pathlib import Path


@pytest.mark.asyncio
async def test_process_text_task():
    # Setup
    service = MagicMock()
    service.voice_service.get_voice.return_value = {
        "voice_id": "v1",
        "language": "german",
        "example_text": "ex",
        "instruct": "inst",
    }
    service.generate_audio = AsyncMock(return_value=Path("test.wav"))

    task = TextTask(text="hello", speaker="v1")
    base_params = MagicMock()
    base_params.model_size = "1.7B"

    # Mock sf.read
    with patch("src.services.orchestrator.ssml.sf") as mock_sf:
        mock_sf.read.return_value = (np.array([0.1, 0.2]), 24000)
        data, sr = await _process_task(service, task, 0, 1, 24000, base_params)
        print(f"DEBUG: data={data}")
        assert data is not None
        assert len(data) == 2

    assert sr == 24000
    service.generate_audio.assert_called_once()


@pytest.mark.asyncio
async def test_process_break_task():
    # Setup
    service = MagicMock()
    task = BreakTask(duration_ms=500)
    base_params = MagicMock()
    sample_rate = 24000

    data, sr = await _process_task(service, task, 0, 1, sample_rate, base_params)

    # 500ms at 24000Hz = 12000 samples
    assert data is not None
    assert len(data) == 12000
    assert sr == 24000
    assert np.all(data == 0)
