import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type = 'table'
AND name = 'risk_explanations'
""")

result = cursor.fetchone()

if result:
    print("✅ risk_explanations table EXISTS")
else:
    print("❌ risk_explanations table NOT FOUND")

connection.close()