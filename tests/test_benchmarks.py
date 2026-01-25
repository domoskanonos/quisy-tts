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
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from project.config import ProjectConfig
from project.engine.qwen import QwenTextToSpeech
from project.schemas import TTSParams
from project.schemas.languages import resolve_language


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def mock_model() -> MagicMock:
    """Create a mock TTS model for benchmarking without actual inference."""
    """Create a mock TTS model for benchmarking without actual inference."""

    mock = MagicMock()
    # Simulate audio output (1 second at 24kHz)
    mock.generate_voice_clone.return_value = (
        [np.zeros(24000, dtype=np.float32)],
        24000,
    )
    mock.generate_voice_design.return_value = (
        [np.zeros(24000, dtype=np.float32)],
        24000,
    )
    mock.generate_custom_voice.return_value = (
        [np.zeros(24000, dtype=np.float32)],
        24000,
    )
    mock.create_voice_clone_prompt.return_value = MagicMock()
    return mock


@pytest.fixture(scope="module")
def tts_engine() -> QwenTextToSpeech:
    """Get TTS engine instance."""
    return QwenTextToSpeech()


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
# Benchmark: Engine Initialization
# =============================================================================


def test_benchmark_engine_init(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
) -> None:
    """Benchmark TTS engine initialization time."""
    """Benchmark TTS engine initialization time."""

    def init_engine() -> QwenTextToSpeech:
        return QwenTextToSpeech()

    result = benchmark(init_engine)
    assert result is not None


# =============================================================================
# Benchmark: Audio Generation (Mocked Model)
# =============================================================================


def test_benchmark_generate_short_text(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
    tts_engine: QwenTextToSpeech,
    mock_model: MagicMock,
) -> None:
    """Benchmark audio generation for short text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    with patch("project.engine.qwen.ModelManager.get_model", return_value=mock_model):
        result = benchmark(tts_engine.generate_audio, SHORT_TEXT, params)

    assert result is not None
    assert len(result) == 2  # noqa: PLR2004 (waveform, sample_rate)


def test_benchmark_generate_medium_text(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
    tts_engine: QwenTextToSpeech,
    mock_model: MagicMock,
) -> None:
    """Benchmark audio generation for medium text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    with patch("project.engine.qwen.ModelManager.get_model", return_value=mock_model):
        result = benchmark(tts_engine.generate_audio, MEDIUM_TEXT, params)

    assert result is not None


def test_benchmark_generate_long_text(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
    tts_engine: QwenTextToSpeech,
    mock_model: MagicMock,
) -> None:
    """Benchmark audio generation for long text."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")

    with patch("project.engine.qwen.ModelManager.get_model", return_value=mock_model):
        result = benchmark(tts_engine.generate_audio, LONG_TEXT, params)

    assert result is not None


# =============================================================================
# Benchmark: Voice Prompt Caching
# =============================================================================


def test_benchmark_voice_prompt_cache_hit(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
    tts_engine: QwenTextToSpeech,
    mock_model: MagicMock,
) -> None:
    """Benchmark voice prompt cache hit performance."""
    ref_audio = (np.zeros(24000, dtype=np.float32), 24000)

    # Prime the cache
    tts_engine._get_or_create_voice_prompt(mock_model, ref_audio, None, True)

    # Benchmark cache hit
    result = benchmark(
        tts_engine._get_or_create_voice_prompt, mock_model, ref_audio, None, True
    )
    assert result is not None


# =============================================================================
# Benchmark: Memory Profiling
# =============================================================================


def test_memory_baseline() -> None:
    """Establish memory baseline before TTS operations."""
    gc.collect()

    tracemalloc.start()

    # Import engine
    engine = QwenTextToSpeech()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Log memory usage
    logger = ProjectConfig.get_logger()
    logger.info(
        f"Memory after engine init: "
        f"current={current / 1024:.2f}KB, peak={peak / 1024:.2f}KB"
    )

    assert engine is not None
    # Engine init should use less than 10MB
    assert current < 10 * 1024 * 1024


# =============================================================================
# Benchmark: Parameter Resolution
# =============================================================================


def test_benchmark_language_resolution(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
) -> None:
    """Benchmark language code resolution."""
    result = benchmark(resolve_language, "de")
    assert result == "German"


def test_benchmark_ttsparams_creation(
    benchmark: "pytest.benchmark.fixture.BenchmarkFixture",
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
    mock_model: MagicMock,
) -> None:
    """Calculate characters per second throughput."""
    params = TTSParams(mode="custom_voice", speaker="eric", language="German")
    text = MEDIUM_TEXT

    with patch("project.engine.qwen.ModelManager.get_model", return_value=mock_model):
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
