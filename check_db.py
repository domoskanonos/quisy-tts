import sqlite3
import os

db_path = "resources/quisy-tts.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, id FROM voices")
    rows = cur.fetchall()
    print("Available voices:")
    for row in rows:
        print(f"Name: {row[0]}, ID: {row[1]}")
    conn.close()
else:
    print(f"DB not found at {db_path}")
