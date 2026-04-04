from src.domain.voice.models import Voice


def test_voice_from_row():
    row = {
        "voice_id": "test",
        "name": "Test Voice",
        "example_text": "Hello",
        "instruct": "Test instruct",
        "language": "german",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
    }
    voice = Voice.from_row(row)
    assert voice.voice_id == "test"
    assert voice.name == "Test Voice"
    assert voice.example_text == "Hello"
    assert voice.instruct == "Test instruct"
    assert voice.language == "german"
    assert voice.created_at == "2023-01-01T00:00:00"
    assert voice.updated_at == "2023-01-01T00:00:00"


def test_get_filename():
    assert Voice.get_filename("test") == "voice_test.wav"
