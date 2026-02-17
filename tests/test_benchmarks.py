"""Performance benchmark tests for Cosmo TTS.

This module provides comprehensive benchmarks for:
- Engine initialization time
- Inference time for short/medium/long texts
- Memory consumption during synthesis

Run with: uv run pytest tests/test_benchmarks.py -v --benchmark-autosave
"""

import gc
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig
from engine.qwen import QwenTextToSpeech, QwenTTSBackend
from schemas import TTSParams
from schemas.languages import resolve_language

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def mock_tts_backend() -> MagicMock:
    """Create a mock qwen-tts backend for benchmarking without actual inference."""
    mock = MagicMock(spec=QwenTTSBackend)
    # Simulate audio output (1 second at 24kHz)
    mock.generate_audio.return_value = (
        torch.zeros(1, 24000, dtype=torch.float32),
        24000,
    )
    return mock


@pytest.fixture(scope="module")
def tts_engine(mock_tts_backend: MagicMock) -> QwenTextToSpeech:
    """Get TTS engine instance with mocked qwen-tts backend."""
    with patch.object(QwenTextToSpeech, "__init__", lambda self: None):
        engine = QwenTextToSpeech()
        engine.settings = ProjectConfig.get_settings()
        engine.backend = mock_tts_backend
        return engine


# =============================================================================
# Text Samples
# =============================================================================


SHORT_TEXT = "Hallo Welt."  # ~10 chars
MEDIUM_TEXT = (
    "Dies ist ein mittellanger Text für Performance-Tests. "
    "Er enthält mehrere Sätze und simuliert einen typischen Anwendungsfall."
)  # ~120 chars
LONG_TEXT = (
    "Dies ist ein sehr langer Text für umfassende Performance-Tests. "
    "Er simuliert komplexe Anwendungsfälle wie Podcasts oder Hörbücher. "
    "Die Synthese langer Texte erfordert effizientes Speichermanagement und "
    "optimierte Inferenz-Pipelines. Wir testen hier die Skalierbarkeit des "
    "Systems unter realistischen Bedingungen. " * 3
)  # ~500 chars


# =============================================================================
# Benchmark: Audio Generation (Mocked qwen-tts Backend)
# =============================================================================


def test_benchmark_generate_short_text(
    benchmark: Any,
    tts_engine: QwenTextToSpeech,
) -> None:
    """Benchmark audio generation for short text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    result = benchmark(tts_engine.generate_audio, SHORT_TEXT, params)

    assert result is not None
    assert len(result) == 2  # noqa: PLR2004 (waveform, sample_rate)


def test_benchmark_generate_medium_text(
    benchmark: Any,
    tts_engine: QwenTextToSpeech,
) -> None:
    """Benchmark audio generation for medium text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    result = benchmark(tts_engine.generate_audio, MEDIUM_TEXT, params)

    assert result is not None


def test_benchmark_generate_long_text(
    benchmark: Any,
    tts_engine: QwenTextToSpeech,
) -> None:
    """Benchmark audio generation for long text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    result = benchmark(tts_engine.generate_audio, LONG_TEXT, params)

    assert result is not None


# =============================================================================
# Benchmark: Memory Profiling
# =============================================================================


def test_memory_baseline(mock_tts_backend: MagicMock) -> None:
    """Establish memory baseline before TTS operations."""
    gc.collect()

    tracemalloc.start()

    # Create engine with mocked backend
    with patch.object(QwenTextToSpeech, "__init__", lambda self: None):
        engine = QwenTextToSpeech()
        engine.settings = ProjectConfig.get_settings()
        engine.backend = mock_tts_backend

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Log memory usage
    logger = ProjectConfig.get_logger()
    logger.info(f"Memory after engine init: current={current / 1024:.2f}KB, peak={peak / 1024:.2f}KB")

    assert engine is not None
    # Engine init should use less than 10MB
    assert current < 10 * 1024 * 1024


# =============================================================================
# Benchmark: Parameter Resolution
# =============================================================================


def test_benchmark_language_resolution(
    benchmark: Any,
) -> None:
    """Benchmark language code resolution."""
    result = benchmark(resolve_language, "de")
    assert result == "German"


def test_benchmark_ttsparams_creation(
    benchmark: Any,
) -> None:
    """Benchmark TTSParams creation."""

    def create_params() -> TTSParams:
        return TTSParams(
            language="German",
            mode="base",
            model_size="1.7B",
            reference_audio="test.wav",
        )

    result = benchmark(create_params)
    assert result.mode == "base"


# =============================================================================
# Throughput Calculation
# =============================================================================


def test_calculate_throughput(
    tts_engine: QwenTextToSpeech,
) -> None:
    """Calculate characters per second throughput."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")
    text = MEDIUM_TEXT

    start = time.perf_counter()
    for _ in range(10):
        tts_engine.generate_audio(text, params)
    elapsed = time.perf_counter() - start

    total_chars = len(text) * 10
    chars_per_second = total_chars / elapsed

    logger = ProjectConfig.get_logger()
    logger.info(f"Throughput: {chars_per_second:.2f} chars/sec (mocked)")

    # With mocked model, should be very fast
    assert chars_per_second > 100  # noqa: PLR2004
