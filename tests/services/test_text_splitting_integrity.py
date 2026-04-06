from pathlib import Path
from services.text_splitter import TextSplitterService


def test_splitter_integrity():
    # 1. Load long text
    text_path = Path("tests/resources/example_text_splitting.txt")
    original_text = text_path.read_text(encoding="utf-8").strip()

    # 2. Split (with new behavior: no splitting)
    splitter = TextSplitterService()
    # Use german as language since it's german text
    chunks = splitter.split(original_text, language="german")

    # 3. Check behavior
    # We expect exactly one chunk containing the original text
    assert len(chunks) == 1
    assert chunks[0] == original_text

    print(f"\nSuccessfully verified that text is NOT split, returning {len(chunks)} chunk(s).")
