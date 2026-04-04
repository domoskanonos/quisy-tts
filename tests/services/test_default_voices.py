from services.default_voices import DEFAULT_VOICES


def test_default_voices_count():
    assert len(DEFAULT_VOICES) == 51
