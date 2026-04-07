import pytest
from src.services.voice_service import VoiceService


@pytest.fixture
def voice_service(tmp_path):
    db_path = tmp_path / "test.db"
    return VoiceService(voices_dir=tmp_path / "voices", db_path=db_path)


def test_create_and_get_voice(voice_service):
    voice = voice_service.create_voice(
        name="test_voice",
        example_text="Dies ist ein Test.",
        instruct="Ein ruhiger Test.",
    )
    assert voice is not None
    assert voice["name"] == "test_voice"

    retrieved = voice_service.get_voice(voice["voice_id"])
    assert retrieved is not None
    assert retrieved["voice_id"] == voice["voice_id"]


def test_list_voices(voice_service):
    voice_service.create_voice(name="v1", example_text="ex1")
    voice_service.create_voice(name="v2", example_text="ex2")

    voices = voice_service.list_voices()
    assert len(voices) == 63 + 2


def test_delete_voice(voice_service):
    voice = voice_service.create_voice(name="v1", example_text="ex1")
    assert voice_service.delete_voice(voice["voice_id"]) is True
    assert voice_service.get_voice(voice["voice_id"]) is None


def test_create_voice_invalid_text(voice_service):
    with pytest.raises(ValueError, match="example_text is mandatory"):
        voice_service.create_voice(name="v1", example_text="")


def test_update_voice(voice_service):
    voice = voice_service.create_voice(name="v1", example_text="ex1")
    updated = voice_service.update_voice(voice["voice_id"], name="v1_new")
    assert updated["name"] == "v1_new"


def test_update_voice_not_found(voice_service):
    assert voice_service.update_voice("nonexistent", name="new") is None
