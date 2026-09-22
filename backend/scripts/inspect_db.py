import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "aurora_cafe.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"=== DATABASE FILE: {db_path} ===")
print(f"Total Tables: {len(tables)}\n")
for table in tables:
    count = cursor.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    print(f" - {table:<30} : {count:>4} baris")

conn.close()
