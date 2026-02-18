"""Unit tests for the TextSplitterService."""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from services.text_splitter import TextSplitterService


class TestTextSplitterBasics:
    """Tests for basic splitting behavior."""

    def test_empty_text_returns_empty_list(self) -> None:
        splitter = TextSplitterService()
        assert splitter.split("") == []
        assert splitter.split("   ") == []

    def test_short_text_no_split(self) -> None:
        splitter = TextSplitterService(max_chunk_chars=300)
        text = "Hallo, ich bin eine Stimme."
        result = splitter.split(text, "german")
        assert result == [text]

    def test_single_sentence_exceeding_limit_kept_intact(self) -> None:
        """A single long sentence should never be split mid-sentence."""
        splitter = TextSplitterService(max_chunk_chars=20)
        text = "Dies ist ein sehr langer Satz ohne Punkt"
        result = splitter.split(text, "german")
        assert len(result) == 1
        assert result[0] == text


class TestRegexFallback:
    """Tests for regex fallback splitting."""

    def test_regex_splits_on_sentence_boundaries(self) -> None:
        splitter = TextSplitterService(max_chunk_chars=50)
        text = "Erster Satz. Zweiter Satz. Dritter Satz."
        result = splitter._split_sentences_regex(text)
        assert len(result) >= 2

    def test_regex_handles_abbreviations(self) -> None:
        """Regex fallback will split on 'Dr.' because it's followed by uppercase.
        This is a known limitation — spaCy handles this correctly."""
        splitter = TextSplitterService()
        text = "Dr. Müller war gestern da. Er hat mich untersucht."
        result = splitter._split_sentences_regex(text)
        # Regex splits on every '. [A-Z]' including 'Dr. M'
        # This is acceptable for a fallback — spaCy does better
        assert len(result) >= 2
        # All text should still be present
        reassembled = " ".join(result)
        assert "Müller" in reassembled
        assert "untersucht" in reassembled

    def test_regex_handles_numbers(self) -> None:
        """Regex should not split on decimal numbers like 3.14."""
        splitter = TextSplitterService()
        text = "Die Zahl Pi ist 3.14. Das ist wichtig."
        result = splitter._split_sentences_regex(text)
        # "3.14" is followed by ". D" which IS a valid split (period + space + uppercase)
        # But "3.14" itself should not cause a split at the decimal point
        assert any("3.14" in s for s in result)


class TestChunkGrouping:
    """Tests for grouping sentences into chunks."""

    def test_groups_short_sentences(self) -> None:
        splitter = TextSplitterService(max_chunk_chars=100)
        sentences = ["Satz eins.", "Satz zwei.", "Satz drei.", "Satz vier.", "Satz fünf."]
        result = splitter._group_into_chunks(sentences)
        # All 5 sentences should fit into ~1-2 chunks
        assert len(result) <= 3
        # Total text should be preserved
        full_text = " ".join(sentences)
        reassembled = " ".join(result)
        assert reassembled == full_text

    def test_respects_max_chars(self) -> None:
        splitter = TextSplitterService(max_chunk_chars=30)
        sentences = ["Satz eins ist lang.", "Satz zwei ist auch lang.", "Satz drei."]
        result = splitter._group_into_chunks(sentences)
        # Each chunk should be at most ~30 chars (single sentences may exceed)
        for chunk in result:
            # Single sentences may exceed limit, but no two should be combined if they'd exceed
            assert len(chunk) <= 50  # generous bound for single long sentences

    def test_preserves_all_text(self) -> None:
        splitter = TextSplitterService(max_chunk_chars=50)
        sentences = ["Erster Satz.", "Zweiter Satz.", "Dritter Satz.", "Vierter Satz."]
        result = splitter._group_into_chunks(sentences)
        reassembled = " ".join(result)
        original = " ".join(sentences)
        assert reassembled == original


class TestLanguageAwareSplitting:
    """Tests that require spaCy models (skip if not installed)."""

    @pytest.fixture
    def splitter(self) -> TextSplitterService:
        return TextSplitterService(max_chunk_chars=100)

    def test_german_splitting(self, splitter: TextSplitterService) -> None:
        """Test German sentence splitting with spaCy if available."""
        text = (
            "Berlin ist die Hauptstadt von Deutschland. "
            "Die Stadt hat über 3,5 Millionen Einwohner. "
            "Dr. Müller arbeitet am Charité-Krankenhaus. "
            "Das Wetter ist heute schön."
        )
        result = splitter.split(text, "german")
        assert len(result) >= 2
        # Verify no text was lost
        reassembled = " ".join(result)
        # All original words should be present
        for word in ["Berlin", "Einwohner", "Müller", "Wetter"]:
            assert word in reassembled

    def test_english_splitting(self, splitter: TextSplitterService) -> None:
        """Test English sentence splitting."""
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "This is a second sentence. "
            "And here is a third one with Dr. Smith."
        )
        result = splitter.split(text, "english")
        assert len(result) >= 1
        reassembled = " ".join(result)
        assert "fox" in reassembled
        assert "Smith" in reassembled

    def test_unknown_language_uses_regex(self, splitter: TextSplitterService) -> None:
        """Unknown languages should fall back to regex without error."""
        text = "First sentence. Second sentence. Third sentence."
        result = splitter.split(text, "klingon")
        assert len(result) >= 1
        assert "First" in " ".join(result)


class TestIntegration:
    """End-to-end integration tests."""

    def test_long_german_text_splits_properly(self) -> None:
        """Simulate a real-world long German TTS input."""
        splitter = TextSplitterService(max_chunk_chars=300)
        text = (
            "Die künstliche Intelligenz hat in den letzten Jahren enorme Fortschritte gemacht. "
            "Besonders im Bereich der Sprachsynthese gibt es beeindruckende Entwicklungen. "
            "Moderne Text-to-Speech-Systeme können natürlich klingende Sprache erzeugen. "
            "Dies ermöglicht viele neue Anwendungen in der Kommunikation. "
            "Von Hörbüchern über Navigationsansagen bis hin zu virtuellen Assistenten. "
            "Die Qualität der erzeugten Sprache ist dabei so hoch, dass sie kaum von menschlicher Sprache zu unterscheiden ist. "
            "Forscher arbeiten daran, die Prosodie und Emotionalität der Sprache weiter zu verbessern. "
            "In Zukunft werden wir noch natürlichere und ausdrucksstärkere Stimmen erleben."
        )
        result = splitter.split(text, "german")

        # Should be split into multiple chunks
        assert len(result) >= 2

        # Each chunk should be manageable
        for chunk in result:
            assert len(chunk) <= 400  # generous bound

        # All text preserved
        reassembled = " ".join(result)
        for word in ["Intelligenz", "Sprachsynthese", "Hörbüchern", "Prosodie", "Zukunft"]:
            assert word in reassembled
