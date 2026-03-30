import pytest
from services.ssml_processor import SSMLProcessor, TextTask, BreakTask
from services.voice_service import VoiceService
from pathlib import Path


# Create a mock voice service that returns a valid voice for "default_014"
class MockVoiceService:
    def get_voice(self, name):
        if name == "default_014":
            return {"voice_id": "default_014"}
        return None


def test_ssml_parsing_full():
    processor = SSMLProcessor(MockVoiceService())  # type: ignore

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
