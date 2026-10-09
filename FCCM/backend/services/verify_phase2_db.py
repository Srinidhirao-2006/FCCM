import sqlite3

DB_PATH = "data/fccm.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

print("\n" + "=" * 70)
print("PHASE 2 DATABASE VERIFICATION")
print("=" * 70)

print("\n--- TRANSACTIONS ---")

cursor.execute("""
    SELECT
        transaction_id,
        customer_id,
        risk_score,
        risk_level,
        fraud_probability,
        actual_fraud
    FROM transactions
    WHERE transaction_id IN (
        'PHASE2_TEST_NORMAL_001',
        'FOUR_MODEL_DEMO_001'
    )
    ORDER BY id DESC
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

print("\n--- ALERTS ---")

cursor.execute("""
    SELECT
        alert_id,
        transaction_id,
        severity,
        risk_score,
        status
    FROM alerts
    WHERE transaction_id IN (
        'PHASE2_TEST_NORMAL_001',
        'FOUR_MODEL_DEMO_001'
    )
    ORDER BY id DESC
""")

alerts = cursor.fetchall()

if alerts:
    for alert in alerts:
        print(alert)
else:
    print("No alerts found.")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)

connection.close()