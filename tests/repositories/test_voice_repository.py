"""Tests for VoiceRepository CRUD operations with a real SQLite test database."""

import sqlite3
from pathlib import Path

import pytest

from src.repositories.voice_repository import VoiceRepository


@pytest.fixture
def test_db(tmp_path: Path) -> Path:
    """Create a fresh test database with schema for each test."""
    db_path = tmp_path / "test_voices.db"
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
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def repo(test_db: Path) -> VoiceRepository:
    """Repository instance using the test database."""
    return VoiceRepository(test_db)


class TestVoiceRepositoryCreate:
    def test_create_voice_success(self, repo: VoiceRepository) -> None:
        voice = repo.create("test_01", "Test Voice", "Hello world", "A calm voice", "german")
        assert voice is not None
        assert voice["voice_id"] == "test_01"
        assert voice["name"] == "Test Voice"
        assert voice["example_text"] == "Hello world"
        assert voice["instruct"] == "A calm voice"
        assert voice["language"] == "german"

    def test_create_voice_duplicate_raises(self, repo: VoiceRepository) -> None:
        repo.create("dup_01", "First", "Hello", None, "german")
        with pytest.raises(sqlite3.IntegrityError):
            repo.create("dup_01", "Second", "World", None, "english")


class TestVoiceRepositoryRead:
    def test_get_by_id_existing(self, repo: VoiceRepository) -> None:
        repo.create("find_01", "Find Me", "Example", "instruct", "english")
        voice = repo.get_by_id("find_01")
        assert voice is not None
        assert voice["name"] == "Find Me"

    def test_get_by_id_nonexistent_returns_none(self, repo: VoiceRepository) -> None:
        assert repo.get_by_id("nonexistent") is None

    def test_get_by_name_existing(self, repo: VoiceRepository) -> None:
        repo.create("name_01", "UniqueName", "Example", None, "german")
        voice = repo.get_by_name("UniqueName")
        assert voice is not None
        assert voice["voice_id"] == "name_01"

    def test_get_by_name_nonexistent_returns_none(self, repo: VoiceRepository) -> None:
        assert repo.get_by_name("DoesNotExist") is None

    def test_list_all_returns_sorted_by_name(self, repo: VoiceRepository) -> None:
        repo.create("c_01", "Charlie", "text", None, "german")
        repo.create("a_01", "Alpha", "text", None, "german")
        repo.create("b_01", "Bravo", "text", None, "german")
        voices = repo.list_all()
        assert len(voices) == 3
        assert voices[0]["name"] == "Alpha"
        assert voices[1]["name"] == "Bravo"
        assert voices[2]["name"] == "Charlie"

    def test_list_all_empty(self, repo: VoiceRepository) -> None:
        assert repo.list_all() == []


class TestVoiceRepositoryUpdate:
    def test_update_name(self, repo: VoiceRepository) -> None:
        repo.create("upd_01", "Old Name", "text", None, "german")
        updated = repo.update("upd_01", {"name": "New Name"})
        assert updated is not None
        assert updated["name"] == "New Name"

    def test_update_multiple_fields(self, repo: VoiceRepository) -> None:
        repo.create("upd_02", "Name", "old text", "old instruct", "german")
        updated = repo.update("upd_02", {"name": "New", "example_text": "new text", "instruct": "new instruct"})
        assert updated is not None
        assert updated["name"] == "New"
        assert updated["example_text"] == "new text"
        assert updated["instruct"] == "new instruct"

    def test_update_invalid_column_raises(self, repo: VoiceRepository) -> None:
        repo.create("upd_03", "Name", "text", None, "german")
        with pytest.raises(ValueError, match="Invalid update columns"):
            repo.update("upd_03", {"voice_id": "hacked"})

    def test_update_nonexistent_returns_none(self, repo: VoiceRepository) -> None:
        result = repo.update("nonexistent", {"name": "X"})
        assert result is None


class TestVoiceRepositoryDelete:
    def test_delete_existing(self, repo: VoiceRepository) -> None:
        repo.create("del_01", "Delete Me", "text", None, "german")
        assert repo.delete("del_01") is True
        assert repo.get_by_id("del_01") is None

    def test_delete_nonexistent_returns_true(self, repo: VoiceRepository) -> None:
        assert repo.delete("nonexistent") is True
