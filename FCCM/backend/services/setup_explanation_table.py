import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS risk_explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    customer_id TEXT,
    final_risk_level TEXT,
    combined_risk_score REAL,
    explanation_count INTEGER DEFAULT 0,
    explanation_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(transaction_id)
        REFERENCES transactions(transaction_id)
)
""")

connection.commit()

print("========================================")
print("RISK EXPLANATION TABLE SETUP")
print("========================================")
print(f"Database: {DB_PATH}")
print("Table: risk_explanations")
print("Status: READY")
print("========================================")

connection.close()