from pathlib import Path
from services.text_splitter import TextSplitterService


def test_splitter_integrity():
    # 1. Load long text
    text_path = Path("tests/resources/example_text_splitting.txt")
    original_text = text_path.read_text(encoding="utf-8").strip()

    # 2. Split
    splitter = TextSplitterService(max_chunk_chars=300)
    # Use german as language since it's german text
    chunks = splitter.split(original_text, language="german")

    # 3. Join
    # TextSplitterService uses ' '.join(current_chunk) for sentences.
    # To compare correctly, we need to normalize whitespace in original and joined
    joined_text = " ".join(chunks)

    # Normalize by splitting on any whitespace and rejoining
    normalized_original = " ".join(original_text.split())
    normalized_joined = " ".join(joined_text.split())

    # 4. Compare
    assert normalized_original == normalized_joined
    print(f"\nSuccessfully verified splitting of {len(original_text)} chars into {len(chunks)} chunks.")
