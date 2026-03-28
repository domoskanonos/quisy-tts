import sqlite3

db_path = "resources/quisy-tts.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

target = "default_035"

print(f"Searching for '{target}'...")

# Check by ID
cur.execute("SELECT * FROM voices WHERE id = ?", (target,))
res_id = cur.fetchone()
print(f"By ID result: {dict(res_id) if res_id else 'None'}")

# Check by Name
cur.execute("SELECT * FROM voices WHERE name = ?", (target,))
res_name = cur.fetchone()
print(f"By Name result: {dict(res_name) if res_name else 'None'}")

conn.close()
