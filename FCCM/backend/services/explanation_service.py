import sqlite3
import json
from pathlib import Path


# ============================================
# DATABASE CONFIGURATION
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"


def get_db_connection():
    """Create and return a SQLite database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================
# SAVE RISK EXPLANATION
# ============================================

def save_explanation(explanation_result):
    """
    Save the complete risk explanation generated
    by risk_explanation.py into SQLite.

    Uses transaction_id as the unique identifier,
    so repeated Kafka processing updates the
    existing explanation instead of creating duplicates.
    """

    transaction_id = explanation_result.get("transaction_id")
    customer_id = explanation_result.get("customer_id")
    final_risk_level = explanation_result.get("final_risk_level")
    combined_risk_score = explanation_result.get("combined_risk_score")
    explanation_count = explanation_result.get("explanation_count", 0)

    explanation_json = json.dumps(
        explanation_result.get("explanations", []),
        ensure_ascii=False
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO risk_explanations (
            transaction_id,
            customer_id,
            final_risk_level,
            combined_risk_score,
            explanation_count,
            explanation_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(transaction_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            final_risk_level = excluded.final_risk_level,
            combined_risk_score = excluded.combined_risk_score,
            explanation_count = excluded.explanation_count,
            explanation_json = excluded.explanation_json,
            updated_at = CURRENT_TIMESTAMP
    """, (
        transaction_id,
        customer_id,
        final_risk_level,
        combined_risk_score,
        explanation_count,
        explanation_json
    ))

    connection.commit()
    connection.close()

    print(f"💾 Risk explanation saved: {transaction_id}")

    return transaction_id


# ============================================
# GET RISK EXPLANATION
# ============================================

def get_explanation(transaction_id):
    """
    Retrieve the stored risk explanation
    for a specific transaction.
    """

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            transaction_id,
            customer_id,
            final_risk_level,
            combined_risk_score,
            explanation_count,
            explanation_json,
            created_at,
            updated_at
        FROM risk_explanations
        WHERE transaction_id = ?
    """, (transaction_id,))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    result = dict(row)

    result["explanations"] = json.loads(
        result["explanation_json"]
    )

    return result


# ============================================
# TEST CONNECTION
# ============================================

if __name__ == "__main__":

    print("========================================")
    print("EXPLANATION SERVICE TEST")
    print("========================================")
    print(f"Database: {DB_PATH}")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM risk_explanations
    """)

    count = cursor.fetchone()[0]

    connection.close()

    print(f"Stored explanations: {count}")
    print("Status: READY")
    print("========================================")