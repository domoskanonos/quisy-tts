import pytest
import sqlite3
from services.voice_search_service import VoiceSearchService


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def service(db_path):
    # Setup database structure
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE voices (id INTEGER PRIMARY KEY, name TEXT, instruct TEXT, example_text TEXT)")
    conn.execute("INSERT INTO voices (name, instruct, example_text) VALUES ('voice1', 'do this', 'example1')")
    conn.execute("INSERT INTO voices (name, instruct, example_text) VALUES ('voice2', 'do that', 'example2')")
    conn.commit()
    conn.close()
    return VoiceSearchService(db_path)


def test_get_top_instruct_terms(service):
    # This should return terms based on the 'instruct' column
    terms = service.get_top_instruct_terms()
    # Check if we got terms.
    assert len(terms) > 0
    # Verify the structure
    assert "term" in terms[0]
    assert "count" in terms[0]

    # Check specific terms extracted from "do this" and "do that"
    term_values = [t["term"] for t in terms]
    # "do" is ignored because it's < 3 chars
    assert "this" in term_values
    assert "that" in term_values
    assert "do" not in term_values


def test_search_fallback(service):
    # This should test the LIKE fallback since we don't have voices_fts table
    results = service.search(terms=["do"], q="voice")
    assert len(results) >= 1
    assert results[0]["name"] in ["voice1", "voice2"]


def test_search_empty_terms_and_query(service):
    # This should hit the 1=1 case
    results = service.search(terms=[], q=None)
    assert len(results) == 2


def test_get_top_instruct_terms_error(service):
    # Setup: drop the table to cause an error
    conn = sqlite3.connect(str(service._db_path))
    conn.execute("DROP TABLE voices")
    conn.commit()
    conn.close()

    terms = service.get_top_instruct_terms()
    assert terms == []


def test_search_fts5_with_query(db_path):
    # Setup database with FTS5
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE voices (id INTEGER PRIMARY KEY, name TEXT, instruct TEXT, example_text TEXT)")
    conn.execute("CREATE VIRTUAL TABLE voices_fts USING fts5(instruct, content='voices', content_rowid='id')")
    conn.execute("INSERT INTO voices (id, name, instruct, example_text) VALUES (1, 'voice1', 'do this', 'example1')")
    conn.execute("INSERT INTO voices_fts (rowid, instruct) VALUES (1, 'do this')")
    conn.commit()
    conn.close()

    service = VoiceSearchService(db_path)

    # Test search with query (q)
    results = service.search(terms=[], q="this")
    assert len(results) == 1
    assert results[0]["name"] == "voice1"


def test_search_error(service):
    # Setup: drop table
    conn = sqlite3.connect(str(service._db_path))
    conn.execute("DROP TABLE voices")
    conn.commit()
    conn.close()

    # The code currently does NOT catch exceptions in the fallback path,
    # so it should raise an exception.
    with pytest.raises(sqlite3.OperationalError):
        service.search(terms=[], q="something")
