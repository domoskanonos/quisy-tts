import pytest
from pathlib import Path
from src.services.ssml_processor import SSMLProcessor, TextTask, BreakTask
from src.core.interfaces import VoiceServiceInterface


# Create a mock voice service that returns a valid voice for "default_014"
class MockVoiceService(VoiceServiceInterface):
    def list_voices(self) -> list[dict]:
        return []

    def get_voice(self, voice_id: str) -> dict | None:
        if voice_id == "default_014":
            return {"voice_id": "default_014"}
        return None

    def get_voice_by_name(self, name: str) -> dict | None:
        return self.get_voice(name)

    def create_voice(
        self,
        name: str,
        example_text: str,
        voice_id: str | None = None,
        instruct: str | None = None,
        description: str | None = None,
        language: str = "german",
    ) -> dict | None:
        return None

    def update_voice(
        self,
        voice_id: str,
        name: str | None = None,
        example_text: str | None = None,
        instruct: str | None = None,
        description: str | None = None,
        language: str | None = None,
    ) -> dict | None:
        return None

    def delete_voice(self, voice_id: str) -> bool:
        return False

    def set_audio(self, voice_id: str, audio_data: bytes, original_filename: str) -> dict | None:
        return None

    def get_audio_path(self, voice_id: str) -> Path | None:
        return None


def test_ssml_parsing_full():
    processor = SSMLProcessor(MockVoiceService())

    xml_content = """<speak>
  <speaker name="default_014">
    Willkommen zum heutigen Gedankenanstoß:
    <break time="800ms"/>
    Sind das meine Wünsche.
    <break time="800ms"/>
    Textblock nach dem Break.
    <break time="800ms"/>
    Ich wünsche dir einen schönen Start in den Tag. Bis bald.
  </speaker>
</speak>"""

    tasks = processor.parse(xml_content)

    # Assertions based on verified logic
    assert len(tasks) == 7  # 4 TextTasks + 3 BreakTasks

    assert isinstance(tasks[0], TextTask)
    assert tasks[0].text == "Willkommen zum heutigen Gedankenanstoß:"
    assert tasks[0].speaker == "default_014"

    assert isinstance(tasks[1], BreakTask)
    assert tasks[1].duration_ms == 800

    assert isinstance(tasks[2], TextTask)
    assert tasks[2].text == "Sind das meine Wünsche."

    assert isinstance(tasks[3], BreakTask)
    assert tasks[3].duration_ms == 800

    assert isinstance(tasks[4], TextTask)
    assert tasks[4].text == "Textblock nach dem Break."

    assert isinstance(tasks[5], BreakTask)
    assert tasks[5].duration_ms == 800

    assert isinstance(tasks[6], TextTask)
    assert tasks[6].text == "Ich wünsche dir einen schönen Start in den Tag. Bis bald."


def test_ssml_invalid_speaker():
    processor = SSMLProcessor(MockVoiceService())
    xml_content = '<speak><speaker name="unknown">Text</speaker></speak>'
    with pytest.raises(ValueError, match="Unknown speaker ID: unknown"):
        processor.parse(xml_string=xml_content)


def test_ssml_no_speaker():
    processor = SSMLProcessor(MockVoiceService())
    xml_content = "<speak>Text without speaker</speak>"
    # Based on the improvement, it now raises ValueError
    with pytest.raises(ValueError, match="Text found without a speaker"):
        processor.parse(xml_string=xml_content)
