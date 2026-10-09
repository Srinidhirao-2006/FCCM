import sqlite3
from pathlib import Path

# ============================================================
# DATABASE PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "fccm.db"
def get_db_connection():
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# SAVE / UPDATE TRANSACTION
# ============================================================

def save_transaction(
    transaction,
    fraud_probability,
    combined_score,
    risk_level,
    source="KAFKA_REAL_TIME"
):
    """
    Insert a transaction into SQLite.

    If the transaction_id already exists, update the existing record.
    This makes Kafka message processing idempotent.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    transaction_id = transaction.get("Transaction_ID")

    cursor.execute(
        """
        INSERT INTO transactions (
            transaction_id,
            customer_id,
            timestamp,
            amount,
            transaction_type,
            merchant_category,
            country,
            is_pep,
            account_age_days,
            transaction_count_24h,
            total_amount_24h,
            device_id,
            ip_risk_score,
            previous_fraud_count,
            actual_fraud,
            fraud_probability,
            risk_score,
            risk_level,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(transaction_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            timestamp = excluded.timestamp,
            amount = excluded.amount,
            transaction_type = excluded.transaction_type,
            merchant_category = excluded.merchant_category,
            country = excluded.country,
            is_pep = excluded.is_pep,
            account_age_days = excluded.account_age_days,
            transaction_count_24h = excluded.transaction_count_24h,
            total_amount_24h = excluded.total_amount_24h,
            device_id = excluded.device_id,
            ip_risk_score = excluded.ip_risk_score,
            previous_fraud_count = excluded.previous_fraud_count,
            actual_fraud = excluded.actual_fraud,
            fraud_probability = excluded.fraud_probability,
            risk_score = excluded.risk_score,
            risk_level = excluded.risk_level,
            source = excluded.source
        """,
        (
            transaction_id,
            transaction.get("Customer_ID"),
            transaction.get("Timestamp"),
            transaction.get("Amount"),
            transaction.get("Transaction_Type"),
            transaction.get("Merchant_Category"),
            transaction.get("Country"),
            transaction.get("Is_PEP", 0),
            transaction.get("Account_Age_Days"),
            transaction.get("Transaction_Count_24H"),
            transaction.get("Total_Amount_24H"),
            transaction.get("Device_ID"),
            transaction.get("IP_Risk_Score"),
            transaction.get("Previous_Fraud_Count"),
            transaction.get("Is_Fraud", 0),
            fraud_probability,
            combined_score,
            risk_level,
            source
        )
    )

    connection.commit()
    connection.close()

    print(f"Transaction saved/updated : {transaction_id}")

    return transaction_id