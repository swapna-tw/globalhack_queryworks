import sqlite3

conn = sqlite3.connect("organization_vault.db")
cursor = conn.cursor()

print("--- EXTERNAL ENTITIES ---")
cursor.execute("SELECT * FROM external_entities;")
for row in cursor.fetchall():
    print(row)

print("\n--- TRANSACTIONS ---")
cursor.execute("SELECT * FROM transactions;")
for row in cursor.fetchall():
    print(row)

conn.close()