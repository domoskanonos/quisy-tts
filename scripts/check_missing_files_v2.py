import sqlite3
from pathlib import Path

voices_dir = Path("voices")
conn = sqlite3.connect("resources/quisy-tts.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, audio_filename FROM voices")

for row in cursor.fetchall():
    filename = row["audio_filename"]
    if filename:
        path = voices_dir / filename
        if not path.exists():
            print(f"Missing file for voice {row['id']}: {filename}")
    else:
        # Check if ID really doesn't have an audio file
        pass
conn.close()
