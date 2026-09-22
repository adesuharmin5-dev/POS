import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "data" / "aurora_cafe.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. Insert Size Modifier (id: 3)
cursor.execute("""
    INSERT OR REPLACE INTO modifiers (id, brand_id, name, min_selection, max_selection, is_active)
    VALUES (3, 1, 'Pilihan Ukuran (Size)', 1, 1, 1)
""")

# 2. Insert Options (id: 7, 8, 9)
options = [
    (7, 3, 'Regular (Standar)', 0.0),
    (8, 3, 'Large (+Rp 5.000)', 5000.0),
    (9, 3, 'Jumbo / Extra (+Rp 8.000)', 8000.0)
]
for opt in options:
    cursor.execute("""
        INSERT OR REPLACE INTO modifier_options (id, modifier_id, name, additional_price)
        VALUES (?, ?, ?, ?)
    """, opt)

# 3. Link Size Modifier to all items (1 to 5)
for item_id in range(1, 6):
    cursor.execute("""
        INSERT OR IGNORE INTO item_modifiers (item_id, modifier_id)
        VALUES (?, 3)
    """, (item_id,))

conn.commit()

# Print results
cursor.execute("SELECT m.name, mo.name, mo.additional_price FROM modifiers m JOIN modifier_options mo ON m.id = mo.modifier_id WHERE m.id = 3")
print("Added Modifier Options:")
for row in cursor.fetchall():
    print(f" - {row[0]} -> {row[1]} (+Rp {row[2]:,.0f})")

cursor.execute("SELECT item_id, modifier_id FROM item_modifiers WHERE modifier_id = 3")
print(f"Linked to {len(cursor.fetchall())} items successfully!")

conn.close()
