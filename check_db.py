import sqlite3
db = sqlite3.connect('backend/cafe.db')
db.row_factory = sqlite3.Row
c = db.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r['name'] for r in c.fetchall()]
print("TABLES:", tables)

# Check if attendance table exists
if 'attendances' in tables or 'attendance' in tables:
    print("ATTENDANCE TABLE EXISTS!")
else:
    print("NO ATTENDANCE TABLE")

# Check employees table columns
c.execute("PRAGMA table_info(employees)")
print("EMPLOYEES COLUMNS:", [r['name'] for r in c.fetchall()])
