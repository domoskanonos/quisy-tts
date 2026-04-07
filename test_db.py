import sqlite3
from pathlib import Path

db_path = Path("data/app_data/quisy-tts.db")
print(f"Path exists: {db_path.exists()}")
print(f"Path is file: {db_path.is_file()}")
print(f"Path is absolute: {db_path.absolute()}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(cursor.fetchall())
    conn.close()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
