import pytest
from schemas.internal import TTSParams


def test_tts_params_copy():
    params = TTSParams(language="english", mode="test", model_size="3B")
    copied = params.model_copy()
    assert copied.language == params.language
    assert copied.mode == params.mode
    assert copied.model_size == params.model_size
    assert copied is not params


def test_tts_params_resolved_language_success():
    # resolve_language for "english" is "english"
    params = TTSParams(language="english")
    assert params.resolved_language == "english"


def test_tts_params_resolved_language_error():
    params = TTSParams(language=None)
    with pytest.raises(ValueError, match="language is not set on TTSParams"):
        _ = params.resolved_language
