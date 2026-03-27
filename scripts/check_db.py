import sqlite3
import pprint

conn = sqlite3.connect("resources/quisy-tts.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, audio_filename FROM voices")
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Filename: {row['audio_filename']}")
conn.close()
