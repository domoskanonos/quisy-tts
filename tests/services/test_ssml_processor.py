"""Tests for SSML processor parsing logic."""

from unittest.mock import MagicMock

import pytest

from services.ssml_processor import BreakTask, SSMLProcessor, TextTask


@pytest.fixture
def processor() -> SSMLProcessor:
    mock_voice_service = MagicMock()
    mock_voice_service.get_voice.return_value = {
        "voice_id": "test_voice",
        "name": "Test Voice",
        "example_text": "Hello",
        "instruct": "A calm voice",
        "language": "german",
    }
    return SSMLProcessor(mock_voice_service)


class TestSSMLParsing:
    def test_single_speaker(self, processor: SSMLProcessor) -> None:
        xml = '<speak><speaker name="test_voice">Hallo Welt</speaker></speak>'
        tasks = processor.parse(xml)
        assert len(tasks) == 1
        assert isinstance(tasks[0], TextTask)
        assert tasks[0].text == "Hallo Welt"
        assert tasks[0].speaker == "test_voice"

    def test_multiple_speakers(self, processor: SSMLProcessor) -> None:
        xml = '<speak><speaker name="test_voice">Hallo</speaker><speaker name="test_voice">Welt</speaker></speak>'
        tasks = processor.parse(xml)
        assert len(tasks) == 2
        assert tasks[0].text == "Hallo"
        assert tasks[1].text == "Welt"

    def test_break_tag_ms(self, processor: SSMLProcessor) -> None:
        xml = '<speak><speaker name="test_voice">Hallo</speaker><break time="500ms"/></speak>'
        tasks = processor.parse(xml)
        assert len(tasks) == 2
        assert isinstance(tasks[1], BreakTask)
        assert tasks[1].duration_ms == 500

    def test_break_tag_s(self, processor: SSMLProcessor) -> None:
        xml = '<speak><speaker name="test_voice">Hallo</speaker><break time="1.5s"/></speak>'
        tasks = processor.parse(xml)
        assert isinstance(tasks[1], BreakTask)
        assert tasks[1].duration_ms == 1500

    def test_invalid_xml_raises_value_error(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="Invalid XML syntax"):
            processor.parse("<not valid xml>")

    def test_missing_speak_root_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="Root tag must be"):
            processor.parse('<speaker name="test_voice">Hallo</speaker>')

    def test_text_without_speaker_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="Text found without a speaker"):
            processor.parse("<speak>Loose text</speak>")

    def test_speaker_missing_name_attr_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="missing 'name' attribute"):
            processor.parse("<speak><speaker>Hallo</speaker></speak>")

    def test_unknown_speaker_raises(self, processor: SSMLProcessor) -> None:
        processor.voice_service.get_voice.return_value = None
        with pytest.raises(ValueError, match="Unknown speaker ID"):
            processor.parse('<speak><speaker name="unknown">Hallo</speaker></speak>')

    def test_unsupported_tag_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="Unsupported tag"):
            processor.parse("<speak><foo>bar</foo></speak>")

    def test_break_missing_time_attr_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="missing 'time' attribute"):
            processor.parse("<speak><break/></speak>")

    def test_break_invalid_time_format_raises(self, processor: SSMLProcessor) -> None:
        with pytest.raises(ValueError, match="Invalid break time format"):
            processor.parse('<speak><break time="5minutes"/></speak>')

    def test_empty_speak_returns_empty_list(self, processor: SSMLProcessor) -> None:
        tasks = processor.parse("<speak></speak>")
        assert tasks == []

    def test_nested_break_between_speakers(self, processor: SSMLProcessor) -> None:
        xml = (
            "<speak>"
            '<speaker name="test_voice">Erste Zeile</speaker>'
            '<break time="1s"/>'
            '<speaker name="test_voice">Zweite Zeile</speaker>'
            "</speak>"
        )
        tasks = processor.parse(xml)
        assert len(tasks) == 3
        assert isinstance(tasks[0], TextTask)
        assert isinstance(tasks[1], BreakTask)
        assert isinstance(tasks[2], TextTask)
        assert tasks[1].duration_ms == 1000
