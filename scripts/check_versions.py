"""Portable search for a text needle inside files.

Replaces the original `grep`-based approach which is not portable on
Windows (editors/terminals may not have grep). Usage:

    python scripts/check_versions.py --needle qwen3_tts --root /path/to/search

Defaults to searching the repository root.
"""

from pathlib import Path
import argparse


def find_occurrences(root: Path, needle: str):
    matches = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf8", errors="ignore")
        except Exception:
            continue
        if needle in text:
            matches.append(path)
    return matches


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--needle", default="qwen3_tts", help="Text to search for")
    p.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Directory to search (defaults to repo root)",
    )
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Root path does not exist: {root}")
        return

    matches = find_occurrences(root, args.needle)
    print(f"Files matching '{args.needle}':")
    if matches:
        for m in matches:
            print(m)
    else:
        print("NONE FOUND")


if __name__ == "__main__":
    main()
