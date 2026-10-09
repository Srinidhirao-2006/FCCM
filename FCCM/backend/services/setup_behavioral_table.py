import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"


connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS behavioral_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    customer_id TEXT UNIQUE NOT NULL,

    transaction_count INTEGER DEFAULT 0,

    behavioral_risk_score REAL DEFAULT 0,
    behavioral_risk_level TEXT,

    is_suspicious INTEGER DEFAULT 0,

    total_transaction_amount REAL DEFAULT 0,
    average_transaction_amount REAL DEFAULT 0,

    maximum_24h_transaction_count INTEGER DEFAULT 0,
    maximum_24h_transaction_amount REAL DEFAULT 0,

    high_value_transaction_count INTEGER DEFAULT 0,
    unique_country_count INTEGER DEFAULT 0,
    unique_device_count INTEGER DEFAULT 0,
    unique_transaction_type_count INTEGER DEFAULT 0,
    structuring_transaction_count INTEGER DEFAULT 0,

    risk_factors_json TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")


connection.commit()

print()
print("=" * 70)
print("BEHAVIORAL ANALYSIS TABLE SETUP")
print("=" * 70)
print(f"Database : {DB_PATH}")
print()
print("Table created successfully: behavioral_analysis")
print("=" * 70)

connection.close()