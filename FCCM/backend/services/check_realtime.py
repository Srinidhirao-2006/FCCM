import sqlite3

connection = sqlite3.connect("data/fccm.db")
cursor = connection.cursor()

query = """
SELECT
    transaction_id,
    customer_id,
    amount,
    risk_level,
    risk_score
FROM transactions
WHERE transaction_id NOT LIKE 'TXN%'
ORDER BY id DESC
"""

cursor.execute(query)

rows = cursor.fetchall()

print("\nREAL-TIME / NON-DATASET TRANSACTIONS")
print("=" * 60)

for row in rows:
    print(row)

print("=" * 60)
print("Total:", len(rows))

connection.close()