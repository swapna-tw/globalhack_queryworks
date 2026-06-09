# database_setup.py
import sqlite3

def setup_sample_database(db_name: str = "organization_vault.db") -> str:
    """Creates the schema and seeds the sample database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS external_entities (
        entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        entity_type TEXT CHECK(entity_type IN ('Vendor', 'Client', 'Partner')),
        contact_email TEXT,
        country TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER,
        transaction_date DATE DEFAULT CURRENT_DATE,
        amount REAL NOT NULL,
        status TEXT CHECK(status IN ('Pending', 'Completed', 'Failed')),
        description TEXT,
        FOREIGN KEY (entity_id) REFERENCES external_entities(entity_id)
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM external_entities;")
    if cursor.fetchone()[0] == 0:
        entities = [
            ('Apex Logistics', 'Vendor', 'billing@apex.com', 'USA'),
            ('Global Tech Corp', 'Client', 'accounts@globaltech.io', 'Canada'),
            ('Acme Manufacturing', 'Vendor', 'supply@acme.com', 'Germany'),
            ('Delta Consulting', 'Partner', 'info@deltaconsult.com', 'UK')
        ]
        cursor.executemany(
            "INSERT INTO external_entities (company_name, entity_type, contact_email, country) VALUES (?, ?, ?, ?);", 
            entities
        )

        transactions = [
            (1, '2026-01-15', 15000.00, 'Completed', 'Monthly fleet shipping fees'),
            (2, '2026-02-10', 45000.50, 'Completed', 'Q1 Software licensing renewal'),
            (3, '2026-03-01', 8200.00, 'Pending', 'Raw materials batch #42'),
            (1, '2026-03-12', 3200.00, 'Failed', 'Urgent courier delivery'),
            (4, '2026-04-18', 12500.00, 'Completed', 'Joint venture marketing consultation')
        ]
        cursor.executemany(
            "INSERT INTO transactions (entity_id, transaction_date, amount, status, description) VALUES (?, ?, ?, ?, ?);", 
            transactions
        )

    conn.commit()
    conn.close()
    return db_name