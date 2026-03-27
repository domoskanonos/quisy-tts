import sqlite3
import os
from pathlib import Path

voices_dir = Path("voices")
conn = sqlite3.connect("resources/quisy-tts.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, name, audio_filename FROM voices WHERE audio_filename IS NOT NULL")

for row in cursor.fetchall():
    filename = row["audio_filename"]
    if filename:
        path = voices_dir / filename
        if not path.exists():
            print(f"Missing file for voice {row['id']} ({row['name']}): {filename}")
        else:
            size = path.stat().st_size
            if size < 1000:  # 1KB is suspiciously small
                print(f"Suspiciously small file for voice {row['id']} ({row['name']}): {filename} ({size} bytes)")
conn.close()
