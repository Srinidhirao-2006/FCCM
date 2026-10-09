import sqlite3
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"

TRANSACTION_ID = "EXPLANATION_DB_TEST_002"

connection = sqlite3.connect(DB_PATH)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

print("=" * 60)
print("EXPLANATION DATABASE TEST")
print("=" * 60)

# Check transaction
cursor.execute("""
    SELECT
        transaction_id,
        customer_id,
        risk_score,
        risk_level,
        fraud_probability
    FROM transactions
    WHERE transaction_id = ?
""", (TRANSACTION_ID,))

transaction = cursor.fetchone()

if transaction:
    print("\n✅ TRANSACTION FOUND")
    print(f"Transaction ID : {transaction['transaction_id']}")
    print(f"Customer ID    : {transaction['customer_id']}")
    print(f"Risk Score     : {transaction['risk_score']}")
    print(f"Risk Level     : {transaction['risk_level']}")
    print(f"ML Probability: {transaction['fraud_probability']}")
else:
    print("\n❌ TRANSACTION NOT FOUND")


# Check explanation
cursor.execute("""
    SELECT
        transaction_id,
        customer_id,
        final_risk_level,
        combined_risk_score,
        explanation_count,
        explanation_json,
        created_at
    FROM risk_explanations
    WHERE transaction_id = ?
""", (TRANSACTION_ID,))

explanation = cursor.fetchone()

if explanation:
    print("\n" + "=" * 60)
    print("✅ RISK EXPLANATION FOUND IN SQLITE")
    print("=" * 60)

    print(f"Transaction ID   : {explanation['transaction_id']}")
    print(f"Customer ID      : {explanation['customer_id']}")
    print(f"Final Risk Level : {explanation['final_risk_level']}")
    print(f"Combined Score   : {explanation['combined_risk_score']}")
    print(f"Explanation Count: {explanation['explanation_count']}")
    print(f"Created At       : {explanation['created_at']}")

    explanations = json.loads(explanation["explanation_json"])

    print("\nWHY WAS THIS TRANSACTION FLAGGED?")

    for i, item in enumerate(explanations, start=1):
        print(f"\n{i}. {item}")

else:
    print("\n❌ RISK EXPLANATION NOT FOUND IN SQLITE")

print("\n" + "=" * 60)

connection.close()