import sqlite3
import os
from pathlib import Path

voices_dir = Path("voices")
conn = sqlite3.connect("resources/quisy-tts.db")
cursor = conn.cursor()
cursor.execute("SELECT id, audio_filename FROM voices WHERE audio_filename IS NOT NULL")

for row in cursor.fetchall():
    vid, filename = row
    if filename:
        path = voices_dir / filename
        if path.exists():
            size = path.stat().st_size
            if size < 1000:  # 1KB
                print(f"Cleaning up voice {vid}: {filename} ({size} bytes)")
                try:
                    path.unlink()
                except Exception as e:
                    print(f"Failed to delete {path}: {e}")
                cursor.execute("UPDATE voices SET audio_filename = NULL WHERE id = ?", (vid,))
conn.commit()
conn.close()
print("Cleanup complete.")
