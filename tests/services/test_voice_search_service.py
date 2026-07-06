"""Tests for VoiceSearchService FTS5 and fallback search."""

import sqlite3
from pathlib import Path

import pytest

from src.services.voice_search_service import VoiceSearchService


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_search.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE voices (
            voice_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            example_text TEXT NOT NULL,
            instruct TEXT,
            language TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE VIRTUAL TABLE voices_fts USING fts5(name, instruct, example_text, content='voices', content_rowid='rowid')"
    )
    voices = [
        ("v01", "Calm Narrator", "Hello world", "A calm male narrator with deep voice", "german"),
        ("v02", "Excited Reporter", "Breaking news", "An excited female reporter", "english"),
        ("v03", "Mystery Voice", "In the shadows", "A mysterious slow-paced male voice", "german"),
    ]
    for vid, name, ex, inst, lang in voices:
        conn.execute(
            "INSERT INTO voices (voice_id, name, example_text, instruct, language, created_at, updated_at) VALUES (?, ?, ?, ?, ?, '2024-01-01', '2024-01-01')",
            (vid, name, ex, inst, lang),
        )
    conn.execute("INSERT INTO voices_fts(voices_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def search_service(test_db: Path) -> VoiceSearchService:
    return VoiceSearchService(test_db)


class TestVoiceSearch:
    def test_search_no_filters_returns_all(self, search_service: VoiceSearchService) -> None:
        results = search_service.search([], None)
        assert len(results) == 3

    def test_search_with_query(self, search_service: VoiceSearchService) -> None:
        results = search_service.search([], "narrator")
        assert len(results) == 1
        assert results[0]["voice_id"] == "v01"

    def test_search_with_terms(self, search_service: VoiceSearchService) -> None:
        results = search_service.search(["calm", "male"], None)
        assert len(results) == 1
        assert results[0]["voice_id"] == "v01"

    def test_search_with_pagination(self, search_service: VoiceSearchService) -> None:
        results = search_service.search([], None, limit=2, offset=0)
        assert len(results) == 2
        results_page2 = search_service.search([], None, limit=2, offset=2)
        assert len(results_page2) == 1

    def test_search_no_match_returns_empty(self, search_service: VoiceSearchService) -> None:
        results = search_service.search([], "nonexistent_xyz")
        assert results == []


class TestTopInstructTerms:
    def test_get_top_instruct_terms(self, search_service: VoiceSearchService) -> None:
        terms = search_service.get_top_instruct_terms()
        assert len(terms) > 0
        assert all("term" in t and "count" in t for t in terms)
        term_words = [t["term"] for t in terms]
        assert "calm" in term_words or "male" in term_words

    def test_get_top_instruct_terms_empty_db(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE voices (voice_id TEXT, name TEXT, example_text TEXT, instruct TEXT, language TEXT, created_at TEXT, updated_at TEXT)"
        )
        conn.commit()
        conn.close()
        service = VoiceSearchService(db_path)
        assert service.get_top_instruct_terms() == []
