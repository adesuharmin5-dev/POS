import sqlite3

conn = sqlite3.connect(r'd:\Aurora\Cafe\backend\data\aurora_cafe.db')
cur = conn.cursor()

# Update users
cur.execute("UPDATE users SET email = REPLACE(email, '@auroracafe.com', '@terasmanis.com'), full_name = REPLACE(full_name, 'Aurora', 'Teras Manis')")

# Update brands
cur.execute("UPDATE brands SET name = 'Teras Manis' WHERE name LIKE '%Aurora%' OR name = ''")

# Update outlets
cur.execute("UPDATE outlets SET name = 'Teras Manis - Outlet Utama' WHERE name LIKE '%Aurora%'")

# Update default receipt settings in settings table if any
cur.execute("UPDATE settings SET setting_value = REPLACE(setting_value, 'AURORA', 'TERAS MANIS') WHERE setting_value LIKE '%AURORA%'")
cur.execute("UPDATE settings SET setting_value = REPLACE(setting_value, 'Aurora', 'Teras Manis') WHERE setting_value LIKE '%Aurora%'")

conn.commit()

cur.execute("SELECT id, username, email, full_name FROM users")
print("Updated users:", cur.fetchall())
cur.execute("SELECT id, name FROM brands")
print("Updated brands:", cur.fetchall())
cur.execute("SELECT id, name FROM outlets")
print("Updated outlets:", cur.fetchall())

conn.close()
print("Database brand update completed successfully.")
