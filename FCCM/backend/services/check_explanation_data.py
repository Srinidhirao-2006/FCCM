import sqlite3
from pathlib import Path
import json

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database path
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"

# Connect to SQLite
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("=" * 70)
print("RISK EXPLANATION DATABASE CHECK")
print("=" * 70)

# Check table
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='risk_explanations'
""")

table = cursor.fetchone()

if not table:
    print("❌ risk_explanations table DOES NOT EXIST")
    connection.close()
    exit()

print("✅ risk_explanations table EXISTS")
print()

# Count records
cursor.execute("""
    SELECT COUNT(*)
    FROM risk_explanations
""")

count = cursor.fetchone()[0]

print(f"Total explanation records: {count}")
print()

# Get latest explanations
cursor.execute("""
    SELECT
        transaction_id,
        customer_id,
        final_risk_level,
        combined_risk_score,
        explanation_count,
        created_at
    FROM risk_explanations
    ORDER BY id DESC
    LIMIT 10
""")

rows = cursor.fetchall()

if not rows:
    print("⚠️ No explanation records found.")
else:
    print("LATEST EXPLANATION RECORDS")
    print("-" * 70)

    for row in rows:
        print(f"Transaction ID     : {row[0]}")
        print(f"Customer ID        : {row[1]}")
        print(f"Final Risk Level   : {row[2]}")
        print(f"Combined Risk      : {row[3]}")
        print(f"Explanation Count  : {row[4]}")
        print(f"Created At         : {row[5]}")
        print("-" * 70)

# Check the specific Kafka test transaction
transaction_id = "PCA_KAFKA_TEST_002"

cursor.execute("""
    SELECT
        transaction_id,
        customer_id,
        final_risk_level,
        combined_risk_score,
        explanation_count,
        explanation_json
    FROM risk_explanations
    WHERE transaction_id = ?
""", (transaction_id,))

record = cursor.fetchone()

print()
print("=" * 70)
print(f"CHECKING: {transaction_id}")
print("=" * 70)

if record:
    print("✅ Explanation record FOUND")
    print()
    print(f"Transaction ID    : {record[0]}")
    print(f"Customer ID       : {record[1]}")
    print(f"Final Risk Level  : {record[2]}")
    print(f"Combined Risk     : {record[3]}")
    print(f"Explanation Count : {record[4]}")
    print()

    print("Stored Explanation JSON:")
    print("-" * 70)

    try:
        explanation = json.loads(record[5])
        print(json.dumps(explanation, indent=4))
    except Exception:
        print(record[5])

else:
    print("⚠️ No explanation record found for this transaction.")
    print()
    print("This means the table exists, but the Kafka consumer")
    print("has not yet stored an explanation for this transaction.")

print("=" * 70)

connection.close()