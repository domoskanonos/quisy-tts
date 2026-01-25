from pathlib import Path


try:
    content = Path("verify_output.txt").read_text(encoding="utf-16le")
except Exception:
    try:
        content = Path("verify_output.txt").read_text(encoding="utf-8")
    except Exception as e:
        content = f"Error reading file: {e}"

print(content)
