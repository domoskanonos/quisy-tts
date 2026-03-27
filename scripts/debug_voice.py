import sqlite3
import pprint

conn = sqlite3.connect("resources/quisy-tts.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, name, audio_filename FROM voices WHERE name LIKE ?", ("%Andreas%",))
row = cursor.fetchone()
if row:
    print(f"Found voice: {dict(row)}")
else:
    print("Voice not found.")
conn.close()
